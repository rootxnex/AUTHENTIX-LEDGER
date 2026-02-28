"""Evidence upload and management router."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_investigator_or_admin, require_any_role
from app.database import get_db
from app.models import Case, EvidenceRecord, EvidenceType, ProfileRecord, User
from app.schemas import EvidenceOut
from app.services.blockchain import get_blockchain_adapter
from app.services.encryption import encrypt_file
from app.services.hashing import sha256_bytes, hash_evidence_bundle
from app.services.storage import upload_bytes
from datetime import datetime, timezone

router = APIRouter(prefix="/evidence", tags=["Evidence"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit per file


@router.post("/upload", response_model=EvidenceOut, status_code=201)
async def upload_evidence(
    case_id: uuid.UUID = Form(...),
    evidence_type: EvidenceType = Form(...),
    profile_id: Optional[uuid.UUID] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator_or_admin),
):
    # Validate case
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Read file
    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit")
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # 1. Compute SHA-256 of ORIGINAL (plaintext) bytes — this is the evidence hash
    file_hash = sha256_bytes(raw_bytes)

    # 2. Check for duplicate evidence
    if db.query(EvidenceRecord).filter(EvidenceRecord.evidence_hash == file_hash).first():
        raise HTTPException(status_code=409, detail="Evidence with this hash already exists")

    # 3. Encrypt before storage
    encrypted = encrypt_file(raw_bytes)

    # 4. Use UUID-based opaque storage key (never exposes original filename)
    storage_key = f"{case_id}/{uuid.uuid4().hex}.enc"
    upload_bytes(storage_key, encrypted, content_type="application/octet-stream")

    # 5. Build and hash evidence bundle for blockchain
    now = datetime.now(timezone.utc).isoformat()
    bundle = {
        "case_id": str(case_id),
        "file_hash": file_hash,
        "evidence_type": evidence_type.value,
        "created_at": now,
    }
    bundle_hash = hash_evidence_bundle(bundle)

    # 6. Anchor on blockchain
    adapter = get_blockchain_adapter()
    profile_record = db.query(ProfileRecord).filter(ProfileRecord.id == profile_id).first() if profile_id else None
    tx_id = await adapter.add_evidence(
        evidence_hash=bundle_hash,
        case_id=str(case_id),
        profile_hash=profile_record.profile_hash if profile_record else None,
        evidence_type=evidence_type.value,
        storage_pointer=storage_key,   # opaque reference, not a URL
        created_by=str(current_user.id),
    )

    # 7. Persist record
    record = EvidenceRecord(
        evidence_hash=bundle_hash,
        original_filename=file.filename or "unknown",
        evidence_type=evidence_type,
        storage_pointer=storage_key,
        file_size_bytes=len(raw_bytes),
        mime_type=file.content_type,
        case_id=case_id,
        profile_id=profile_id,
        created_by_id=current_user.id,
        blockchain_tx_id=tx_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/case/{case_id}", response_model=list[EvidenceOut])
def list_evidence_by_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return db.query(EvidenceRecord).filter(EvidenceRecord.case_id == case_id).all()


@router.get("/{evidence_id}", response_model=EvidenceOut)
def get_evidence(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    rec = db.query(EvidenceRecord).filter(EvidenceRecord.id == evidence_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return rec


@router.get("/{evidence_id}/verify")
async def verify_evidence(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """Verify that evidence hash matches blockchain record — chain-of-custody check."""
    rec = db.query(EvidenceRecord).filter(EvidenceRecord.id == evidence_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Evidence not found")

    adapter = get_blockchain_adapter()
    result = await adapter.verify_evidence_hash(rec.evidence_hash)
    return {
        "evidence_id": str(evidence_id),
        "evidence_hash": rec.evidence_hash,
        "blockchain_verified": result["found"],
        "blockchain_metadata": result.get("metadata"),
    }
