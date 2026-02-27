"""Pydantic schemas — request/response contracts."""
import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models import UserRole, CaseStatus, ProfileStatus, EvidenceType, Platform


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.INVESTIGATOR
    unit: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")
        return v


class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    unit: Optional[str]
    is_active: bool
    created_at: datetime


# ── Case ──────────────────────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    fir_number: Optional[str] = None
    owner_unit: str


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None


class CaseOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    title: str
    description: Optional[str]
    fir_number: Optional[str]
    owner_unit: str
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID
    blockchain_tx_id: Optional[str]
    profile_count: Optional[int] = 0
    evidence_count: Optional[int] = 0


# ── Profile Analysis ──────────────────────────────────────────────────────────

class ProfileAnalyzeRequest(BaseModel):
    profile_url: str
    platform: Platform
    case_id: uuid.UUID
    # Optional pre-fetched profile data (for richer AI analysis)
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    account_age_days: Optional[int] = None
    bio_text: Optional[str] = None
    username: Optional[str] = None


class RiskFactor(BaseModel):
    name: str
    contribution: float  # SHAP value
    direction: str       # "increases_risk" | "decreases_risk"
    description: str


class ProfileAnalyzeResponse(BaseModel):
    profile_hash: str
    profile_url: str
    platform: str
    risk_score: float
    risk_level: str        # LOW / MEDIUM / HIGH / CRITICAL
    risk_factors: List[RiskFactor]
    status: ProfileStatus
    blockchain_tx_id: Optional[str]
    record_id: uuid.UUID
    analyzed_at: datetime


class ProfileOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    profile_hash: str
    profile_url: str
    platform: Platform
    status: ProfileStatus
    risk_score: Optional[float]
    risk_factors: Optional[str]
    case_id: uuid.UUID
    created_at: datetime
    blockchain_tx_id: Optional[str]


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    evidence_hash: str
    original_filename: str
    evidence_type: EvidenceType
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    case_id: uuid.UUID
    profile_id: Optional[uuid.UUID]
    created_at: datetime
    blockchain_tx_id: Optional[str]


# ── Registry ──────────────────────────────────────────────────────────────────

class RegistrySearchResult(BaseModel):
    hash: str
    hash_type: str   # "profile" | "evidence"
    found: bool
    records: List[Any] = []


# ── Report ────────────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    case_id: uuid.UUID
    include_evidence_hashes: bool = True
    include_risk_breakdown: bool = True
    investigator_notes: Optional[str] = None


class ReportOut(BaseModel):
    report_id: str
    case_id: uuid.UUID
    generated_at: datetime
    download_url: str
    hash_proof: str    # SHA-256 of the PDF itself


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
