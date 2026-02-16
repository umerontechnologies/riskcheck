from __future__ import annotations

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def _wrap(text: str, max_chars: int):
    text = (text or "").strip()
    if not text:
        return []
    # simple wrap without external deps
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 <= max_chars:
            line = (line + " " + word).strip()
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def _risk_color(risk_level: str):
    rl = (risk_level or "").lower()
    if rl == "high":
        return colors.HexColor("#dc2626")
    if rl == "medium":
        return colors.HexColor("#d97706")
    if rl == "low":
        return colors.HexColor("#16a34a")
    return colors.HexColor("#64748b")  # unknown


def build_report_pdf(payload: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # tokens
    left = 18 * mm
    right = width - 18 * mm
    y = height - 18 * mm

    grade = payload.get("grade", "Unverified")
    confidence = int(payload.get("confidence", 0) or 0)
    risk_level = payload.get("risk_level", "Unknown")
    entity_type = payload.get("entity_type", "")
    entity_value = payload.get("entity_value", "")
    created = payload.get("created_at") or (datetime.utcnow().isoformat() + "Z")

    risk_col = _risk_color(risk_level)

    # Header bar
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(0, height - 28 * mm, width, 28 * mm, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, height - 18 * mm, "RiskCheck — Risk Report")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#cbd5e1"))
    c.drawString(left, height - 23 * mm, f"Generated: {created}")

    y = height - 36 * mm

    # Risk badge
    c.setFillColor(risk_col)
    c.roundRect(left, y - 10 * mm, 44 * mm, 10 * mm, 4 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left + 6 * mm, y - 7 * mm, (risk_level or "Unknown").upper())

    # Summary box
    y -= 14 * mm
    c.setFillColor(colors.HexColor("#ffffff"))
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.roundRect(left, y - 26 * mm, right - left, 26 * mm, 4 * mm, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left + 6 * mm, y - 8 * mm, "Summary")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(left + 6 * mm, y - 14 * mm, f"Grade: {grade}")
    c.drawString(left + 60 * mm, y - 14 * mm, f"Confidence: {confidence}%")
    c.drawString(left + 6 * mm, y - 20 * mm, f"Entity: {entity_type} — {entity_value}")

    y -= 34 * mm

    # Warnings + what’s missing/ok
    signals = payload.get("signals", []) or []
    highs = [s for s in signals if (s.get("status") or "").lower() == "high"]
    lows = [s for s in signals if (s.get("status") or "").lower() == "low"]
    unknowns = [s for s in signals if (s.get("status") or "").lower() == "unknown"]

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(left, y, "Highlights")
    y -= 6 * mm

    def bullet(title, items, color_hex):
        nonlocal y
        if y < 35 * mm:
            c.showPage()
            y = height - 18 * mm
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor(color_hex))
        c.drawString(left, y, title)
        y -= 5 * mm
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#334155"))
        if not items:
            c.drawString(left + 4 * mm, y, "• None")
            y -= 5 * mm
            return
        for it in items[:5]:
            name = it.get("name") or it.get("title") or "Signal"
            note = it.get("note") or it.get("detail") or ""
            line = f"• {name}: {note}".strip()
            for ln in _wrap(line, 105)[:2]:
                c.drawString(left + 4 * mm, y, ln)
                y -= 4.5 * mm
            y -= 1 * mm

    bullet("⚠️ High-risk warnings", highs, "#dc2626")
    bullet("✅ Positive signals", lows, "#16a34a")
    bullet("❓ Missing / Unverified", unknowns, "#64748b")

    y -= 2 * mm

    # Signals table
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(left, y, "Signals (details)")
    y -= 7 * mm

    for s in signals[:25]:
        if y < 30 * mm:
            c.showPage()
            y = height - 18 * mm
        name = s.get("name") or s.get("title") or "Signal"
        status = s.get("status") or s.get("level") or "Unknown"
        note = s.get("note") or s.get("detail") or ""

        st = status.lower()
        dot = "#64748b"
        if st == "high": dot = "#dc2626"
        elif st == "medium": dot = "#d97706"
        elif st == "low": dot = "#16a34a"

        c.setFillColor(colors.HexColor(dot))
        c.circle(left + 1.5 * mm, y + 1.3 * mm, 1.2 * mm, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left + 5 * mm, y, name)

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawRightString(right, y, status)

        y -= 4.8 * mm
        for ln in _wrap(note, 110)[:3]:
            c.drawString(left + 5 * mm, y, ln)
            y -= 4.2 * mm
        y -= 2 * mm

    # Recommendation
    rec = payload.get("recommendation") or payload.get("rationale") or ""
    if y < 45 * mm:
        c.showPage()
        y = height - 18 * mm

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(left, y, "Recommendation")
    y -= 7 * mm

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#334155"))
    for ln in _wrap(rec, 110)[:12]:
        c.drawString(left, y, ln)
        y -= 5 * mm

    # Footer disclaimer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(
        left,
        12 * mm,
        "Disclaimer: RiskCheck estimates risk from public signals and provided evidence. It does not label anyone as a scammer.",
    )

    c.save()
    return buf.getvalue()
