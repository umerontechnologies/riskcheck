import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .footprint import (
    domain_rdap_age_days,
    email_mx_signal,
    google_enabled,
    google_footprint_summary,
    phone_signal,
    url_reachability_signal,
)

Status = str  # "High" | "Medium" | "Low" | "Unknown"


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def normalize_url(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    # Add https for url-like strings without scheme
    if not re.match(r"^https?://", s, re.I) and ("." in s or "/" in s):
        s = "https://" + s

    try:
        p = urlparse(s)
        if p.scheme and p.netloc:
            netloc = p.netloc.lower()
            path = p.path.rstrip("/")
            return f"{p.scheme.lower()}://{netloc}{path}" + (f"?{p.query}" if p.query else "")
    except Exception:
        pass

    return s


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def normalize_phone(value: str) -> str:
    # Remove spaces and dashes; keep +
    s = (value or "").strip()
    s = re.sub(r"[\s\-()]+", "", s)
    return s


def entity_key_for(entity_type: str, entity_value: str) -> Tuple[str, str]:
    et = (entity_type or "").strip().lower()
    raw = (entity_value or "").strip()

    if et in {"whatsapp", "telegram"}:
        phone_norm = normalize_phone(raw)
        # Use validated E.164 if possible
        ps = phone_signal(phone_norm)
        key = ps.get("e164") if ps.get("ok") and ps.get("valid") and ps.get("e164") else phone_norm
        return phone_norm, key

    if et == "email":
        em = normalize_email(raw)
        return em, em

    # Default: treat as URL-ish
    url = normalize_url(raw)
    p = urlparse(url)
    if p.netloc:
        key = (p.netloc + p.path).lower().rstrip("/")
        # Special-case Facebook profile.php?id=...
        if "facebook.com" in p.netloc.lower() and p.path.lower().endswith("/profile.php"):
            # Try to extract id
            qs = p.query or ""
            m = re.search(r"(?:^|&)id=(\d+)", qs)
            if m:
                key = f"facebook_profile_id:{m.group(1)}"
        return url, key

    # Non-url fallback: hash it
    key = hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:24]
    return raw, key


def _facebook_entity_kind(url: str) -> str:
    """Return 'profile' | 'page' | 'group' | 'unknown' based on URL patterns."""
    u = (url or "").lower()
    if "facebook.com" not in u:
        return "unknown"
    if "/groups/" in u:
        return "group"
    if "profile.php" in u:
        return "profile"
    # Heuristic: pages often have /pages/ or no obvious signals
    if "/pages/" in u:
        return "page"
    return "page"


def _signal(name: str, status: Status, note: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"name": name, "status": status, "note": note}
    if meta:
        out["meta"] = meta
    return out


def _risk_points_from_status(status: Status) -> int:
    if status == "High":
        return 4
    if status == "Medium":
        return 2
    return 0


def score_multi_platform(
    *,
    entity_type: str,
    entity_value: str,
    evidence: Optional[Dict[str, Any]] = None,
    seller_phone: Optional[str] = None,
    seller_email: Optional[str] = None,
    seller_website: Optional[str] = None,
    linked_accounts: Optional[List[Dict[str, str]]] = None,
    community: Optional[Dict[str, int]] = None,
    media: Optional[Dict[str, Any]] = None,
) -> Tuple[str, int, List[Dict[str, Any]], str, str]:
    """Return (risk_level, confidence, signals, rationale, grade)."""

    evidence = evidence or {}
    linked_accounts = linked_accounts or []
    community = community or {"approved": 0, "pending": 0}
    media = media or {}

    normalized_entity, entity_key = entity_key_for(entity_type, entity_value)

    signals: List[Dict[str, Any]] = []
    risk_points = 0
    info_points = 25

    # 1) Basic identifier validity
    if entity_type in {"facebook", "instagram", "website", "olx", "daraz", "amazon", "ebay", "aliexpress", "pakwheels", "autotrader", "craigslist", "gumtree", "carousell"}:
        url = normalize_url(normalized_entity)
        if urlparse(url).netloc:
            signals.append(_signal("URL validity", "Low", "Looks like a valid URL.", {"normalized": url}))
            info_points += 5
        else:
            signals.append(_signal("URL validity", "High", "Not a valid URL format."))
            risk_points += 4
    elif entity_type in {"whatsapp", "telegram"}:
        ps = phone_signal(normalized_entity)
        if ps.get("ok") and ps.get("valid"):
            signals.append(_signal("Phone format validity", "Low", f"Valid phone number ({ps.get('region')}).", {"e164": ps.get("e164")}))
            info_points += 5
        else:
            signals.append(_signal("Phone format validity", "Medium", ps.get("note") or "Could not validate phone format."))
            risk_points += 2
    else:
        signals.append(_signal("Identifier", "Unknown", "Unsupported platform type. We'll do best-effort checks."))

    # 2) Platform-specific classification
    if entity_type == "facebook":
        kind = _facebook_entity_kind(normalized_entity)
        note = "Facebook Page URL." if kind == "page" else ("Facebook Profile URL." if kind == "profile" else ("Facebook Group URL (limited public signals)." if kind == "group" else "Facebook link."))
        status = "Unknown" if kind == "group" else "Low"
        signals.append(_signal("Entity type", status, note, {"kind": kind}))
        if kind == "group":
            info_points += 2
        else:
            info_points += 3

    # 3) URL reachability (for URLs)
    parsed = urlparse(normalize_url(normalized_entity))
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        reach = url_reachability_signal(parsed.geturl())
        signals.append(_signal("Website reachability", reach.get("status", "Unknown"), reach.get("note", ""), {"final_url": reach.get("final_url")}))
        risk_points += _risk_points_from_status(reach.get("status", "Unknown"))
        if reach.get("ok"):
            info_points += 6

        # Domain age (best-effort) for non-platform websites only
        if entity_type in {"website"}:
            age = domain_rdap_age_days(parsed.hostname or "")
            if age is None:
                signals.append(_signal("Domain age", "Unknown", "Domain age not available."))
            else:
                info_points += 6
                if age < 30:
                    signals.append(_signal("Domain age", "High", f"Domain appears newly registered (~{age} days)."))
                    risk_points += 4
                elif age < 180:
                    signals.append(_signal("Domain age", "Medium", f"Domain is relatively new (~{age} days)."))
                    risk_points += 2
                else:
                    signals.append(_signal("Domain age", "Low", f"Domain has existed for ~{age} days."))

    # 4) Internet footprint (Google CSE)
    # Main entity footprint
    footprint = google_footprint_summary(normalized_entity, platform_hint=entity_type)
    if not footprint.get("enabled"):
        signals.append(_signal("Internet footprint", "Unknown", "Google footprint search is disabled (missing API key/CX)."))
    else:
        total = int(footprint.get("total") or 0)
        neg = int(footprint.get("negative_hits") or 0)
        top = footprint.get("top_domains") or []

        info_points += 18

        if total == 0:
            signals.append(_signal("Internet footprint", "Medium", "No public results found for this identifier (harder to verify)."))
            risk_points += 2
        elif neg > 0:
            signals.append(_signal(
                "Internet footprint",
                "High",
                f"Public search results include {neg} potential complaint/scam mention(s).",
                {"results": total, "top_domains": top},
            ))
            risk_points += 4
        else:
            signals.append(_signal(
                "Internet footprint",
                "Low",
                f"Found {total} public result(s). No obvious scam keywords in top results.",
                {"results": total, "top_domains": top},
            ))

    # 5) Seller contact signals (phone/email/website)
    if seller_phone:
        ps = phone_signal(seller_phone)
        if ps.get("ok") and ps.get("valid"):
            info_points += 4
            fp = google_footprint_summary(ps.get("e164") or seller_phone, platform_hint=None)
            if fp.get("enabled"):
                info_points += 8
                if int(fp.get("negative_hits") or 0) > 0:
                    signals.append(_signal("Phone footprint", "High", "Phone appears in public results with scam/complaint keywords.", {"top_domains": fp.get("top_domains", [])}))
                    risk_points += 4
                elif int(fp.get("total") or 0) == 0:
                    signals.append(_signal("Phone footprint", "Medium", "Phone has no public footprint (harder to verify)."))
                    risk_points += 2
                else:
                    signals.append(_signal("Phone footprint", "Low", "Phone has public footprint (more verifiable).", {"top_domains": fp.get("top_domains", [])}))
            else:
                signals.append(_signal("Phone footprint", "Unknown", "Google footprint search disabled."))
        else:
            signals.append(_signal("Phone format", "Medium", ps.get("note") or "Could not validate phone."))
            risk_points += 2

    if seller_email:
        em = normalize_email(seller_email)
        mx = email_mx_signal(em)
        if mx.get("ok") is True and mx.get("valid") is True:
            signals.append(_signal("Email domain (MX)", "Low", mx.get("note") or "Email domain can receive mail."))
            info_points += 4
        elif mx.get("ok") is True and mx.get("valid") is False:
            signals.append(_signal("Email domain (MX)", "Medium", mx.get("note") or "No MX records."))
            risk_points += 2
        else:
            signals.append(_signal("Email domain (MX)", "Unknown", mx.get("note") or "MX lookup unavailable."))

        fp = google_footprint_summary(em)
        if fp.get("enabled"):
            info_points += 8
            if int(fp.get("negative_hits") or 0) > 0:
                signals.append(_signal("Email footprint", "High", "Email appears in public results with scam/complaint keywords.", {"top_domains": fp.get("top_domains", [])}))
                risk_points += 4
            elif int(fp.get("total") or 0) == 0:
                signals.append(_signal("Email footprint", "Medium", "Email has no public footprint (harder to verify)."))
                risk_points += 2
            else:
                signals.append(_signal("Email footprint", "Low", "Email has public footprint (more verifiable).", {"top_domains": fp.get("top_domains", [])}))
        else:
            signals.append(_signal("Email footprint", "Unknown", "Google footprint search disabled."))

    if seller_website:
        sw = normalize_url(seller_website)
        if urlparse(sw).netloc:
            info_points += 4
            reach = url_reachability_signal(sw)
            signals.append(_signal("Seller website reachability", reach.get("status", "Unknown"), reach.get("note", "")))
            risk_points += _risk_points_from_status(reach.get("status", "Unknown"))

            fp = google_footprint_summary(sw)
            if fp.get("enabled"):
                info_points += 8
                if int(fp.get("negative_hits") or 0) > 0:
                    signals.append(_signal("Seller website footprint", "High", "Website appears in public results with scam/complaint keywords.", {"top_domains": fp.get("top_domains", [])}))
                    risk_points += 4
                elif int(fp.get("total") or 0) == 0:
                    signals.append(_signal("Seller website footprint", "Medium", "Website has no public footprint (harder to verify)."))
                    risk_points += 2
                else:
                    signals.append(_signal("Seller website footprint", "Low", "Website has public footprint (more verifiable).", {"top_domains": fp.get("top_domains", [])}))
            else:
                signals.append(_signal("Seller website footprint", "Unknown", "Google footprint search disabled."))
        else:
            signals.append(_signal("Seller website", "Medium", "Website is not a valid URL."))
            risk_points += 2

    # 6) Cross-platform accounts
    if linked_accounts:
        info_points += 3
        negative_any = 0
        checked = 0
        for acc in linked_accounts[:3]:
            v = (acc.get("value") or "").strip()
            if not v:
                continue
            checked += 1
            fp = google_footprint_summary(v, platform_hint=acc.get("platform"))
            if fp.get("enabled"):
                info_points += 4
                if int(fp.get("negative_hits") or 0) > 0:
                    negative_any += 1
        if checked == 0:
            signals.append(_signal("Cross-platform accounts", "Unknown", "Related accounts list is empty."))
        elif negative_any > 0:
            signals.append(_signal("Cross-platform accounts", "High", f"{negative_any} related account(s) have complaint/scam keywords in public results."))
            risk_points += 4
        else:
            signals.append(_signal("Cross-platform accounts", "Low", f"{checked} related account(s) provided."))
    else:
        signals.append(_signal("Cross-platform accounts", "Unknown", "No related accounts provided."))

    # 7) Community reports
    approved = int(community.get("approved", 0) or 0)
    pending = int(community.get("pending", 0) or 0)

    if approved > 0:
        signals.append(_signal("Community reports (approved)", "High", f"{approved} approved report(s) exist for this entity."))
        risk_points += 4
        info_points += 8
    else:
        signals.append(_signal("Community reports (approved)", "Low", "No approved community reports found."))
        info_points += 5

    if pending > 0:
        signals.append(_signal("Community reports (pending)", "Medium", f"{pending} pending report(s) (not counted as truth)."))
        risk_points += 2
        info_points += 3
    else:
        signals.append(_signal("Community reports (pending)", "Low", "No pending community reports."))
        info_points += 2

    # 8) Screenshot / media evidence
    if media.get("provided"):
        info_points += 4
        reuse = int(media.get("reuse_count", 0) or 0)
        if reuse > 0:
            signals.append(_signal("User screenshot reuse", "High", f"This screenshot has appeared in {reuse} other check(s) (possible reused ad image)."))
            risk_points += 4
        else:
            signals.append(_signal("User screenshot provided", "Low", "Screenshot stored for similarity checks (no reuse detected yet)."))
    else:
        signals.append(_signal("User screenshot", "Unknown", "No screenshot provided."))

    # 9) Evidence checklist (user-provided)
    # We only score what user answered.
    def tri(name: str, field: str, yes_low_note: str, no_med_note: str) -> None:
        nonlocal risk_points, info_points
        if field not in evidence:
            return
        info_points += 2
        val = evidence.get(field)
        if val is True:
            signals.append(_signal(name, "Low", yes_low_note))
        elif val is False:
            signals.append(_signal(name, "Medium", no_med_note))
            risk_points += 2
        else:
            signals.append(_signal(name, "Unknown", "Not sure."))

    tri("About section", "has_about", "About section is present.", "About section missing (less transparent).")
    tri("Reviews visible", "has_reviews", "Reviews are visible.", "Reviews are not visible.")
    tri("Address/location", "has_address", "Address/location is provided.", "No location provided.")
    tri("Phone or email on page", "has_phone_or_email", "Contact info is shown.", "No contact info shown.")
    tri("Posts history", "has_posts_older_than_6_months", "Account has older posts (history exists).", "No old posts / very new account.")
    tri("Recent activity", "has_recent_posts_last_30_days", "Recent activity exists.", "No recent activity.")

    if evidence.get("asked_advance_payment") is True:
        signals.append(_signal("Advance payment request", "High", "Seller asked for advance payment (common scam indicator)."))
        risk_points += 6
        info_points += 2

    # 10) Transaction stakes
    pr = (evidence.get("price") or evidence.get("price_range") or "")
    try:
        amt = int(re.sub(r"[^0-9]", "", str(pr))) if pr else None
    except Exception:
        amt = None

    if amt is not None:
        info_points += 2
        if amt >= 100000:
            signals.append(_signal("Transaction stakes", "Medium", "High amount — be extra careful (prefer escrow/COD)."))
            risk_points += 2
        elif amt >= 20000:
            signals.append(_signal("Transaction stakes", "Unknown", "Medium amount — risk depends on payment method."))
        else:
            signals.append(_signal("Transaction stakes", "Low", "Low amount reduces impact but does not confirm safety."))
    else:
        signals.append(_signal("Transaction stakes", "Unknown", "No stake signal provided."))

    # Final risk level
    # Critical triggers
    critical_high = any(s["status"] == "High" and s["name"] in {"Advance payment request", "Community reports (approved)", "User screenshot reuse"} for s in signals)

    if critical_high or risk_points >= 10:
        risk_level = "High"
        grade = "High Risk"
    elif risk_points >= 5:
        risk_level = "Medium"
        grade = "Warning"
    else:
        # If we have enough verification and very low risk points, allow Low
        verification = 0
        for s in signals:
            if s["name"] in {"Internet footprint", "Website reachability", "Phone footprint", "Email footprint", "Seller website footprint"} and s["status"] == "Low":
                verification += 1
        if risk_points <= 1 and verification >= 2:
            risk_level = "Low"
            grade = "Good"
        else:
            risk_level = "Unknown"
            grade = "Unverified"

    confidence = _clamp(info_points, 10, 95)

    # Rationale
    if risk_level == "High":
        rationale = (
            "High-risk signals were detected. Avoid advance payments. Prefer Cash on Delivery (COD), platform-protected "
            "checkout, or escrow. Ask for strong proof (invoice, live video with today's date, verified business address) "
            "and verify contacts across platforms."
        )
    elif risk_level == "Medium":
        rationale = (
            "Warning-level signals were found. This is not a verdict, but risk is higher than normal. "
            "Prefer COD/escrow, verify the seller's identity, and do not send advance payments."
        )
    else:
        rationale = (
            "Unverified. Risk level is Unknown based on available signals. We do not label anyone as a scammer — we assess "
            "risk and uncertainty. Prefer COD/escrow, ask for proof (invoice, live video), and avoid advance payment."
        )

    # Add short transparency note
    if not google_enabled():
        rationale += " (Tip: enable Google footprint search by adding GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX in backend .env.)"

    return risk_level, confidence, signals, rationale, grade
