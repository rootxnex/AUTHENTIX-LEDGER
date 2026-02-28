"""Profiles router — risk analysis and profile management."""
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_investigator_or_admin, require_any_role
from app.database import get_db
from app.models import Case, ProfileRecord, ProfileStatus, User
from app.schemas import ProfileAnalyzeRequest, ProfileAnalyzeResponse, ProfileOut, RiskFactor
from app.services.ai_client import score_profile
from app.services.blockchain import get_blockchain_adapter
from app.services.hashing import canonical_profile_id

router = APIRouter(prefix="/profiles", tags=["Profile Analysis"])


@router.post("/analyze", response_model=ProfileAnalyzeResponse, status_code=201)
async def analyze_profile(
    body: ProfileAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator_or_admin),
):
    # Validate case exists
    case = db.query(Case).filter(Case.id == body.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Generate canonical hash for this profile (PII-safe)
    profile_hash = canonical_profile_id(body.platform.value, body.profile_url)

    # Check if already analyzed in this case
    existing = db.query(ProfileRecord).filter(
        ProfileRecord.profile_hash == profile_hash,
        ProfileRecord.case_id == body.case_id,
    ).first()

    # Run AI scoring
    profile_data = {
        "platform": body.platform.value,
        "follower_count": body.follower_count or 0,
        "following_count": body.following_count or 0,
        "post_count": body.post_count or 0,
        "account_age_days": body.account_age_days or 365,
        "bio_text": body.bio_text or "",
        "username": body.username or "",
    }
    ai_result = score_profile(profile_data)
    risk_score = ai_result["risk_score"]
    risk_level = ai_result["risk_level"]
    risk_factors = ai_result["risk_factors"]

    # Determine status
    profile_status = ProfileStatus.FLAGGED if risk_score >= 50 else ProfileStatus.PENDING

    # Anchor on blockchain
    adapter = get_blockchain_adapter()
    tx_id = await adapter.register_profile(
        profile_hash=profile_hash,
        platform=body.platform.value,
        risk_score=risk_score,
        case_id=str(body.case_id),
        created_by=str(current_user.id),
    )

    if existing:
        # Update existing record
        existing.risk_score = risk_score
        existing.risk_factors = json.dumps(risk_factors)
        existing.status = profile_status
        existing.blockchain_tx_id = tx_id
        db.commit()
        db.refresh(existing)
        record = existing
    else:
        record = ProfileRecord(
            profile_hash=profile_hash,
            profile_url=body.profile_url,
            platform=body.platform,
            status=profile_status,
            risk_score=risk_score,
            risk_factors=json.dumps(risk_factors),
            case_id=body.case_id,
            created_by_id=current_user.id,
            blockchain_tx_id=tx_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return ProfileAnalyzeResponse(
        profile_hash=profile_hash,
        profile_url=body.profile_url,
        platform=body.platform.value,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_factors=[RiskFactor(**f) for f in risk_factors],
        status=profile_status,
        blockchain_tx_id=tx_id,
        record_id=record.id,
        analyzed_at=datetime.now(timezone.utc),
    )


@router.get("/case/{case_id}", response_model=list[ProfileOut])
def list_profiles_by_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return db.query(ProfileRecord).filter(ProfileRecord.case_id == case_id).all()


@router.get("/{profile_hash}", response_model=list[ProfileOut])
def get_profile_by_hash(
    profile_hash: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    records = db.query(ProfileRecord).filter(ProfileRecord.profile_hash == profile_hash).all()
    if not records:
        raise HTTPException(status_code=404, detail="Profile hash not found in registry")
    return records


@router.patch("/{profile_id}/status")
async def update_profile_status(
    profile_id: uuid.UUID,
    new_status: ProfileStatus = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator_or_admin),
):
    record = db.query(ProfileRecord).filter(ProfileRecord.id == profile_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Profile record not found")

    record.status = new_status
    adapter = get_blockchain_adapter()
    tx_id = await adapter.update_profile_status(record.profile_hash, new_status.value, str(current_user.id))
    record.blockchain_tx_id = tx_id
    db.commit()
    return {"status": new_status.value, "blockchain_tx_id": tx_id}


@router.get("/{profile_hash}/history")
async def get_profile_chain_history(
    profile_hash: str,
    _: User = Depends(require_any_role),
):
    """Return full blockchain ledger history for a profile hash (audit trail)."""
    adapter = get_blockchain_adapter()
    history = await adapter.get_profile_history(profile_hash)
    return {"profile_hash": profile_hash, "history": history}
