"""SQLAlchemy ORM models for AUTHENTIX LEDGER."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Enumerations ──────────────────────────────────────────────────────────────

class UserRole(str, PyEnum):
    ADMIN = "ADMIN"
    INVESTIGATOR = "INVESTIGATOR"
    AUDITOR = "AUDITOR"


class CaseStatus(str, PyEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ProfileStatus(str, PyEnum):
    PENDING = "PENDING"
    FLAGGED = "FLAGGED"
    VERIFIED = "VERIFIED"
    DISMISSED = "DISMISSED"


class EvidenceType(str, PyEnum):
    SCREENSHOT = "SCREENSHOT"
    JSON_EXPORT = "JSON_EXPORT"
    REPORT = "REPORT"
    OTHER = "OTHER"


class Platform(str, PyEnum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TELEGRAM = "telegram"
    OTHER = "other"


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.INVESTIGATOR)
    unit: Mapped[str] = mapped_column(String(128), nullable=True)  # police station / cyber cell
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    cases: Mapped[list["Case"]] = relationship("Case", back_populates="owner")
    evidence_records: Mapped[list["EvidenceRecord"]] = relationship("EvidenceRecord", back_populates="created_by_user")


# ── Case ──────────────────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    fir_number: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    owner_unit: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), nullable=False, default=CaseStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    blockchain_tx_id: Mapped[str] = mapped_column(String(256), nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="cases")
    profiles: Mapped[list["ProfileRecord"]] = relationship("ProfileRecord", back_populates="case")
    evidence_records: Mapped[list["EvidenceRecord"]] = relationship("EvidenceRecord", back_populates="case")


# ── ProfileRecord ─────────────────────────────────────────────────────────────

class ProfileRecord(Base):
    __tablename__ = "profile_records"
    __table_args__ = (UniqueConstraint("profile_hash", "case_id", name="uq_profile_case"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    profile_url: Mapped[str] = mapped_column(String(512), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    status: Mapped[ProfileStatus] = mapped_column(Enum(ProfileStatus), nullable=False, default=ProfileStatus.PENDING)
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    risk_factors: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    blockchain_tx_id: Mapped[str] = mapped_column(String(256), nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="profiles")
    evidence_records: Mapped[list["EvidenceRecord"]] = relationship("EvidenceRecord", back_populates="profile")


# ── EvidenceRecord ────────────────────────────────────────────────────────────

class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    evidence_type: Mapped[EvidenceType] = mapped_column(Enum(EvidenceType), nullable=False)
    storage_pointer: Mapped[str] = mapped_column(String(512), nullable=False)  # opaque MinIO object key
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profile_records.id"), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    blockchain_tx_id: Mapped[str] = mapped_column(String(256), nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="evidence_records")
    profile: Mapped["ProfileRecord"] = relationship("ProfileRecord", back_populates="evidence_records")
    created_by_user: Mapped["User"] = relationship("User", back_populates="evidence_records")


# ── AuditLog ──────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
