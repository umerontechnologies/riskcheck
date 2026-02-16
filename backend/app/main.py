import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from .config import ADMIN_TOKEN, FRONTEND_ORIGINS, UPLOAD_DIR
from .db import db_conn, init_db, json_dumps, json_loads, now_iso
from .media import compute_phash, store_upload_bytes
from .pdf import build_report_pdf
from .schemas import (
    CheckRequest,
    CheckResponse,
    CommunityReportRequest,
    CommunityReportResponse,
    UploadResponse,
)
from .scoring import entity_key_for, score_multi_platform


app = FastAPI(
    title="RiskCheck API",
    version="1.0.0",
    description="RiskCheck — risk assessment signals for online buying (UMERON Technologies)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


# main.py (replace only the upload endpoint)

@app.post("/api/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")

        # Optional: limit size (e.g. 8MB)
        max_bytes = 8 * 1024 * 1024
        if len(data) > max_bytes:
            raise HTTPException(status_code=413, detail="File too large (max 8MB)")

        # Optional: only allow images
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are allowed")

        sha256, saved_path = store_upload_bytes(
            data,
            UPLOAD_DIR,
            original_filename=file.filename,
            mime_type=file.content_type,
        )

        p_hash = compute_phash(saved_path)

        with db_conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO media(sha256, phash, filename, mime_type, size_bytes, created_at)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    sha256,
                    p_hash,
                    file.filename or f"upload-{sha256}",
                    file.content_type or "application/octet-stream",
                    len(data),
                    now_iso(),
                ),
            )

        return UploadResponse(
            sha256=sha256,
            url=f"/api/file/{sha256}",
            filename=file.filename,
            size_bytes=len(data),
        )

    except HTTPException:
        raise
    except Exception as ex:
        # This prevents “silent 500” with no clue
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(ex)}")



@app.get("/api/file/{sha256}")
def get_file(sha256: str) -> FileResponse:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM media WHERE sha256=?", (sha256,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        # Find file on disk by trying common extensions
        base = Path(UPLOAD_DIR) / sha256
        candidates = list(base.parent.glob(f"{sha256}.*"))
        if not candidates:
            # Fallback: if stored without extension
            if base.exists():
                candidates = [base]
        if not candidates:
            raise HTTPException(status_code=404, detail="File missing on disk")

        path = candidates[0]
        return FileResponse(path, media_type=row["mime_type"], filename=row["filename"])


def _count_community(conn, entity_type: str, entity_key: str) -> Dict[str, int]:
    approved = conn.execute(
        "SELECT COUNT(*) AS c FROM community_reports WHERE entity_type=? AND entity_key=? AND status='approved'",
        (entity_type, entity_key),
    ).fetchone()["c"]
    pending = conn.execute(
        "SELECT COUNT(*) AS c FROM community_reports WHERE entity_type=? AND entity_key=? AND status='pending'",
        (entity_type, entity_key),
    ).fetchone()["c"]
    return {"approved": int(approved or 0), "pending": int(pending or 0)}


def _attachment_reuse_count(conn, entity_type: str, entity_key: str, sha256s: List[str]) -> int:
    if not sha256s:
        return 0
    placeholders = ",".join(["?"] * len(sha256s))
    rows = conn.execute(
        f"""
        SELECT DISTINCT entity_key FROM entity_media
        WHERE media_sha256 IN ({placeholders})
        """,
        tuple(sha256s),
    ).fetchall()

    other_keys = {r["entity_key"] for r in rows if r["entity_key"] != entity_key}
    return len(other_keys)


@app.post("/api/check", response_model=CheckResponse)
def check(req: CheckRequest) -> CheckResponse:
    normalized_value, entity_key = entity_key_for(req.entity_type, req.entity_value)

    with db_conn() as conn:
        comm = _count_community(conn, req.entity_type, entity_key)
        reuse_count = _attachment_reuse_count(conn, req.entity_type, entity_key, req.attachment_sha256s or [])

        # Score
        evidence: Dict[str, Any] = dict(req.evidence or {})
        if req.intent:
            evidence["intent"] = req.intent
        if req.price_range:
            evidence["price_range"] = req.price_range

        risk_level, confidence, signals, rationale, grade = score_multi_platform(
            entity_type=req.entity_type,
            entity_value=normalized_value,
            evidence=evidence,
            seller_phone=req.seller_phone,
            seller_email=req.seller_email,
            seller_website=req.seller_website,
            linked_accounts=[x.dict() for x in (req.linked_accounts or [])],
            community={
                "approved": comm["approved"],
                "pending": comm["pending"],
            },
            media={
                "reuse_count": reuse_count,
            },
        )

        # Persist submission
        cur = conn.execute(
            """
            INSERT INTO submissions(
                created_at,
                entity_type, entity_key, entity_value,
                intent, price_range,
                seller_phone, seller_email, seller_website,
                user_contact,
                risk_level, confidence, grade, rationale,
                signals_json, evidence_json, attachment_sha256s_json, linked_accounts_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                now_iso(),
                req.entity_type,
                entity_key,
                normalized_value,
                req.intent,
                req.price_range,
                req.seller_phone,
                req.seller_email,
                req.seller_website,
                req.user_contact,
                risk_level,
                int(confidence),
                grade,
                rationale,
                json_dumps(signals),
                json_dumps(req.evidence or {}),
                json_dumps(req.attachment_sha256s or []),
                json_dumps([x.dict() for x in (req.linked_accounts or [])]),
            ),
        )
        submission_id = int(cur.lastrowid)

        # Link attachments to entity for future reuse detection
        for sha in req.attachment_sha256s or []:
            conn.execute(
                "INSERT OR IGNORE INTO entity_media(entity_type, entity_key, media_sha256, created_at) VALUES(?,?,?,?)",
                (req.entity_type, entity_key, sha, now_iso()),
            )

    return CheckResponse(
        id=submission_id,
        entity_type=req.entity_type,
        entity_value=normalized_value,
        risk_level=risk_level,
        confidence=int(confidence),
        grade=grade,
        signals=signals,
        rationale=rationale,
        community={"approved_count": comm["approved"], "pending_count": comm["pending"]},
    )


@app.get("/api/report/{submission_id}/pdf")
def report_pdf(submission_id: int) -> Response:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Convert sqlite row to dict
        submission: Dict[str, Any] = dict(row)

        # Attach community counts
        comm = _count_community(conn, submission["entity_type"], submission["entity_key"])
        submission["community_approved_count"] = comm["approved"]
        submission["community_pending_count"] = comm["pending"]

        # Signals and evidence as parsed
        submission["signals"] = json_loads(submission.get("signals_json"))
        submission["evidence"] = json_loads(submission.get("evidence_json"))

    pdf_bytes = build_report_pdf(submission)
    headers = {"Content-Disposition": f"attachment; filename=riskcheck-report-{submission_id}.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@app.post("/api/community/report", response_model=CommunityReportResponse)
def community_report(req: CommunityReportRequest) -> CommunityReportResponse:
    normalized_value, entity_key = entity_key_for(req.entity_type, req.entity_value)

    with db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO community_reports(
                created_at,
                entity_type, entity_key, entity_value,
                category, description, amount,
                evidence_url, reporter_contact,
                attachment_sha256s_json,
                linked_accounts_json,
                status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                now_iso(),
                req.entity_type,
                entity_key,
                normalized_value,
                req.category,
                req.description,
                req.amount,
                req.evidence_url,
                req.reporter_contact,
                json_dumps(req.attachment_sha256s or []),
                json_dumps([x.dict() for x in (req.linked_accounts or [])]),
                "pending",
            ),
        )
        report_id = int(cur.lastrowid)

        # Link attachments to entity (useful for reuse signals)
        for sha in req.attachment_sha256s or []:
            conn.execute(
                "INSERT OR IGNORE INTO entity_media(entity_type, entity_key, media_sha256, created_at) VALUES(?,?,?,?)",
                (req.entity_type, entity_key, sha, now_iso()),
            )

    return CommunityReportResponse(id=report_id, status="pending")


def _require_admin(token: Optional[str]) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin actions disabled")
    if not token or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")


@app.post("/api/admin/reports/{report_id}/approve")
def approve_report(report_id: int, token: Optional[str] = None) -> Dict[str, Any]:
    _require_admin(token)
    with db_conn() as conn:
        conn.execute("UPDATE community_reports SET status='approved' WHERE id=?", (report_id,))
        row = conn.execute("SELECT status FROM community_reports WHERE id=?", (report_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
    return {"ok": True, "id": report_id, "status": row["status"]}


@app.post("/api/admin/reports/{report_id}/reject")
def reject_report(report_id: int, token: Optional[str] = None) -> Dict[str, Any]:
    _require_admin(token)
    with db_conn() as conn:
        conn.execute("UPDATE community_reports SET status='rejected' WHERE id=?", (report_id,))
        row = conn.execute("SELECT status FROM community_reports WHERE id=?", (report_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
    return {"ok": True, "id": report_id, "status": row["status"]}
