from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LinkedAccount(BaseModel):
    platform: Optional[str] = None
    value: str


class CheckRequest(BaseModel):
    entity_type: str = Field(..., description="Platform key, e.g. facebook, whatsapp, website")
    entity_value: str = Field(..., description="Main identifier/link/handle")

    # Optional context
    intent: Optional[str] = None
    price_range: Optional[str] = None

    # Seller contact (optional but recommended)
    seller_phone: Optional[str] = None
    seller_email: Optional[str] = None
    seller_website: Optional[str] = None

    # Optional user contact (NOT used for seller scoring)
    user_contact: Optional[str] = None

    evidence: Optional[Dict[str, Any]] = None
    linked_accounts: Optional[List[LinkedAccount]] = None
    attachment_sha256s: Optional[List[str]] = None


class Signal(BaseModel):
    name: str
    status: str
    note: str
    meta: Optional[Dict[str, Any]] = None


class CheckResponse(BaseModel):
    id: int
    entity_type: str
    entity_value: str
    risk_level: str
    confidence: int
    grade: str
    signals: List[Signal]
    rationale: str
    community: Dict[str, int]


class UploadResponse(BaseModel):
    sha256: str
    filename: str
    mime_type: Optional[str] = None
    size_bytes: int


class CommunityReportRequest(BaseModel):
    entity_type: str
    entity_value: str
    category: str
    description: str

    amount: Optional[int] = None
    evidence_url: Optional[str] = None
    reporter_contact: Optional[str] = None

    linked_accounts: Optional[List[LinkedAccount]] = None
    attachment_sha256s: Optional[List[str]] = None


class CommunityReportResponse(BaseModel):
    id: int
    status: str


class ApproveRejectRequest(BaseModel):
    status: str = Field(..., description="approved or rejected")
