"""External footprint helpers.

This module is intentionally conservative:
- Uses Google Programmable Search Engine (Custom Search JSON API) only when keys exist.
- Avoids scraping private data. For platforms like Facebook groups, we rely on public web footprint.
- For URLs, we only perform safe HTTP(S) requests to public hosts.

All functions return best-effort signals and never raise exceptions to callers.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from .config import GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX, GOOGLE_CSE_GL, GOOGLE_CSE_HL, HTTP_TIMEOUT_S, SEARCH_CACHE_TTL_S
from .db import db_conn, json_dumps, json_loads, now_iso


NEGATIVE_KEYWORDS = [
    # English
    "scam",
    "scammer",
    "fraud",
    "fake",
    "complaint",
    "ripoff",
    "cheat",
    "cheater",
    "phishing",
    "spammer",
    "blacklist",
    "beware",
    "not delivered",
    "non delivery",
    "non-delivery",
    "advance payment",
    "advance-pay",
    "chargeback",
    # Urdu / Roman Urdu (common Pakistan signals)
    "dhoka",
    "fraudiya",
    "fraud",
    "chor",
    "farib",
    "thug",
    "dhokebaaz",
]


@dataclass
class GoogleResult:
    enabled: bool
    query: str
    total: int
    items: List[Dict[str, str]]
    fetched_at: str
    error: Optional[str] = None


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


def google_enabled() -> bool:
    return bool(GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX)


def _cache_get(query_hash: str) -> Optional[Dict[str, Any]]:
    try:
        with db_conn() as conn:
            row = conn.execute(
                "SELECT response_json, created_at FROM search_cache WHERE query_hash = ?",
                (query_hash,),
            ).fetchone()
            if not row:
                return None
            created_at = row["created_at"]
            # created_at stored as ISO
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age_s = (datetime.now(timezone.utc) - created_dt).total_seconds()
            if age_s > SEARCH_CACHE_TTL_S:
                return None
            return json_loads(row["response_json"], None)
    except Exception:
        return None


def _cache_set(query_hash: str, query: str, payload: Dict[str, Any]) -> None:
    try:
        with db_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO search_cache(query_hash, query, response_json, created_at) VALUES(?,?,?,?)",
                (query_hash, query, json_dumps(payload), now_iso()),
            )
            conn.commit()
    except Exception:
        pass


def google_cse_search(query: str, *, num: int = 8, gl: Optional[str] = None, hl: Optional[str] = None) -> GoogleResult:
    """Run a Google Programmable Search query via the JSON API.

    Returns an object with:
      - enabled: False when keys missing
      - total: totalResults from searchInformation
      - items: {title, link, snippet}

    Uses sqlite cache to reduce API usage.
    """

    gl = gl or GOOGLE_CSE_GL
    hl = hl or GOOGLE_CSE_HL

    if not google_enabled():
        return GoogleResult(
            enabled=False,
            query=query,
            total=0,
            items=[],
            fetched_at=now_iso(),
            error="Google CSE is not configured (missing GOOGLE_CSE_API_KEY / GOOGLE_CSE_CX)",
        )

    safe_num = max(1, min(int(num), 10))
    cache_key = _hash(f"v1|{query}|{safe_num}|{gl}|{hl}")

    cached = _cache_get(cache_key)
    if cached:
        return GoogleResult(
            enabled=bool(cached.get("enabled", True)),
            query=cached.get("query", query),
            total=int(cached.get("total", 0)),
            items=list(cached.get("items", [])),
            fetched_at=cached.get("fetched_at", now_iso()),
            error=cached.get("error"),
        )

    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_CSE_API_KEY,
                "cx": GOOGLE_CSE_CX,
                "q": query,
                "num": safe_num,
                "gl": gl,
                "hl": hl,
            },
            timeout=HTTP_TIMEOUT_S,
        )
        data: Dict[str, Any]
        try:
            data = resp.json()
        except Exception:
            data = {}

        if resp.status_code != 200:
            err = data.get("error", {}).get("message") if isinstance(data, dict) else None
            out = GoogleResult(
                enabled=True,
                query=query,
                total=0,
                items=[],
                fetched_at=now_iso(),
                error=err or f"Google API error (HTTP {resp.status_code})",
            )
            _cache_set(cache_key, query, out.__dict__)
            return out

        total_raw = (
            data.get("searchInformation", {}).get("totalResults")
            if isinstance(data, dict)
            else "0"
        )
        try:
            total = int(str(total_raw))
        except Exception:
            total = 0

        items: List[Dict[str, str]] = []
        for it in (data.get("items") or []) if isinstance(data, dict) else []:
            if not isinstance(it, dict):
                continue
            items.append(
                {
                    "title": str(it.get("title", ""))[:200],
                    "link": str(it.get("link", ""))[:500],
                    "snippet": str(it.get("snippet", ""))[:500],
                }
            )

        out = GoogleResult(
            enabled=True,
            query=query,
            total=total,
            items=items,
            fetched_at=now_iso(),
            error=None,
        )
        _cache_set(cache_key, query, out.__dict__)
        return out

    except Exception as e:
        out = GoogleResult(
            enabled=True,
            query=query,
            total=0,
            items=[],
            fetched_at=now_iso(),
            error=str(e),
        )
        _cache_set(cache_key, query, out.__dict__)
        return out


def _domain_from_url(url: str) -> Optional[str]:
    try:
        p = urlparse(url)
        host = p.hostname
        if not host:
            return None
        return host.lower()
    except Exception:
        return None


def _is_public_host(hostname: str) -> bool:
    """Basic SSRF safety: block localhost/private IP literals.

    Note: We do not resolve DNS here to avoid DNS-based SSRF complexity.
    """

    try:
        # If hostname is an IP literal, reject private/loopback/link-local/multicast.
        ip = ipaddress.ip_address(hostname)
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except Exception:
        # Not an IP literal: allow (DNS could still point to private IP, but this is a reasonable first layer).
        return hostname not in {"localhost"}


def safe_http_get(url: str, *, max_bytes: int = 600_000) -> Dict[str, Any]:
    """Fetch a URL with safety and small limits.

    Returns dict with ok, status_code, final_url, https, error, content_type.
    """

    url = (url or "").strip()
    if not url:
        return {"ok": False, "error": "empty url"}

    p = urlparse(url)
    if p.scheme not in {"http", "https"}:
        return {"ok": False, "error": "unsupported scheme"}

    host = p.hostname
    if not host or not _is_public_host(host):
        return {"ok": False, "error": "blocked host"}

    headers = {
        "User-Agent": "RiskCheckBot/1.0 (+https://umerontechnologies.com)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_S, allow_redirects=True, stream=True)
        content = b""
        try:
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                content += chunk
                if len(content) >= max_bytes:
                    break
        finally:
            resp.close()

        return {
            "ok": True,
            "status_code": int(resp.status_code),
            "final_url": str(resp.url),
            "https": str(resp.url).lower().startswith("https://"),
            "content_type": str(resp.headers.get("content-type", ""))[:100],
            "bytes": len(content),
            "text_sample": content[:2000].decode("utf-8", errors="ignore"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def url_reachability_signal(url: str) -> Dict[str, Any]:
    """Simple URL reachability + HTTPS presence."""

    res = safe_http_get(url)
    if not res.get("ok"):
        return {
            "ok": False,
            "status": "Unknown",
            "note": f"Could not fetch URL: {res.get('error', 'unknown error')}",
        }

    status_code = int(res.get("status_code", 0) or 0)
    https = bool(res.get("https"))

    if 200 <= status_code < 400 and https:
        return {
            "ok": True,
            "status": "Low",
            "note": f"URL responded (HTTP {status_code}). HTTPS is present.",
            "final_url": res.get("final_url"),
        }

    if 200 <= status_code < 400 and not https:
        return {
            "ok": True,
            "status": "Medium",
            "note": f"URL responded (HTTP {status_code}) but HTTPS is not used.",
            "final_url": res.get("final_url"),
        }

    return {
        "ok": True,
        "status": "Medium",
        "note": f"URL responded with HTTP {status_code}.",
        "final_url": res.get("final_url"),
    }


def domain_rdap_age_days(domain: str) -> Optional[int]:
    """Best-effort domain age (days) using public RDAP.

    Returns None when unavailable.
    """

    domain = (domain or "").strip().lower()
    if not domain or "." not in domain:
        return None

    # Avoid SSRF: rdap.org is fixed.
    try:
        resp = requests.get(f"https://rdap.org/domain/{domain}", timeout=HTTP_TIMEOUT_S)
        if resp.status_code != 200:
            return None
        data = resp.json() if isinstance(resp.json(), dict) else None
        if not isinstance(data, dict):
            return None
        events = data.get("events") or []
        created = None
        for ev in events:
            if not isinstance(ev, dict):
                continue
            if str(ev.get("eventAction", "")).lower() in {"registration", "registered", "domain registration", "created"}:
                created = ev.get("eventDate")
                break
        if not created:
            return None
        created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - created_dt
        return max(0, int(age.total_seconds() // 86400))
    except Exception:
        return None


def email_mx_signal(email: str) -> Dict[str, Any]:
    """Check if the email domain has MX records.

    This is NOT a guarantee the mailbox exists; it only suggests the domain can receive email.
    """

    email = (email or "").strip().lower()
    if "@" not in email:
        return {"ok": False, "valid": False, "note": "Invalid email format."}
    domain = email.split("@", 1)[1]

    try:
        import dns.resolver  # type: ignore

        answers = dns.resolver.resolve(domain, "MX")
        mx = [str(r.exchange).rstrip(".") for r in answers]
        if mx:
            return {"ok": True, "valid": True, "note": f"Email domain has MX record(s): {', '.join(mx[:3])}."}
        return {"ok": True, "valid": False, "note": "No MX records found."}
    except Exception as e:
        # dnspython may not be installed.
        return {"ok": False, "valid": None, "note": f"MX lookup unavailable: {e}"}


def phone_signal(phone: str, default_region: str = "PK") -> Dict[str, Any]:
    """Validate & normalize a phone number using phonenumbers."""

    raw = (phone or "").strip()
    if not raw:
        return {"ok": False, "valid": False, "note": "Empty phone."}

    try:
        import phonenumbers  # type: ignore

        num = phonenumbers.parse(raw, default_region)
        valid = phonenumbers.is_valid_number(num)
        e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
        region = phonenumbers.region_code_for_number(num)
        if valid:
            return {"ok": True, "valid": True, "e164": e164, "region": region, "note": f"Valid number ({region})."}
        return {"ok": True, "valid": False, "e164": e164, "region": region, "note": "Invalid phone number."}
    except Exception as e:
        return {"ok": False, "valid": None, "note": f"Phone validation unavailable: {e}"}


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
URL_RE = re.compile(r"\bhttps?://[^\s<>'\"]+", re.I)
# This is intentionally simple; phone parsing uses phonenumbers later.
PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-()]{8,}\d)")


def extract_candidates(text: str) -> Dict[str, List[str]]:
    text = text or ""
    emails = list({m.group(0) for m in EMAIL_RE.finditer(text)})
    urls = list({m.group(0) for m in URL_RE.finditer(text)})
    phones = list({m.group(0) for m in PHONE_RE.finditer(text)})
    return {"emails": emails[:10], "urls": urls[:10], "phones": phones[:10]}


def analyze_search_items(items: List[Dict[str, str]]) -> Dict[str, Any]:
    neg_hits = 0
    top_domains: List[str] = []
    domain_counts: Dict[str, int] = {}

    for it in items or []:
        blob = f"{it.get('title','')} {it.get('snippet','')}".lower()
        if any(k in blob for k in NEGATIVE_KEYWORDS):
            neg_hits += 1

        link = it.get("link") or ""
        dom = _domain_from_url(link)
        if dom:
            domain_counts[dom] = domain_counts.get(dom, 0) + 1

    for dom, _cnt in sorted(domain_counts.items(), key=lambda x: (-x[1], x[0])):
        top_domains.append(dom)

    return {
        "negative_hits": neg_hits,
        "top_domains": top_domains[:8],
        "domain_counts": domain_counts,
    }


def google_footprint_summary(value: str, *, platform_hint: Optional[str] = None) -> Dict[str, Any]:
    """Return an internet footprint summary for a value.

    Output:
      {
        enabled: bool,
        query: str,
        total: int,
        negative_hits: int,
        top_domains: [..],
        error: str|null
      }

    We do NOT return raw result snippets to avoid leaking personal data.
    """

    value = (value or "").strip()
    if not value:
        return {"enabled": google_enabled(), "total": 0, "negative_hits": 0, "top_domains": [], "error": "empty"}

    # Build a query that is stable across inputs.
    # If value is URL, remove scheme to broaden hits.
    q = value
    if value.lower().startswith("http://") or value.lower().startswith("https://"):
        q = value.split("//", 1)[1]

    if platform_hint:
        q = f"{q} {platform_hint}".strip()

    # Quote the core token to reduce noisy results.
    if " " not in q:
        query = f'"{q}"'
    else:
        query = q

    res = google_cse_search(query, num=8)
    if not res.enabled:
        return {
            "enabled": False,
            "query": query,
            "total": 0,
            "negative_hits": 0,
            "top_domains": [],
            "error": res.error,
        }

    analysis = analyze_search_items(res.items)
    return {
        "enabled": True,
        "query": query,
        "total": int(res.total),
        "negative_hits": int(analysis.get("negative_hits", 0)),
        "top_domains": list(analysis.get("top_domains", [])),
        "error": res.error,
    }
