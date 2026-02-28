"""Registry router — hash search across blockchain and DB."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.rbac import require_any_role
from app.database import get_db
from app.models import EvidenceRecord, ProfileRecord, User
from app.schemas import RegistrySearchResult
from app.services.blockchain import get_blockchain_adapter

router = APIRouter(prefix="/registry", tags=["Hash Registry"])


@router.get("/search", response_model=RegistrySearchResult)
async def search_hash(
    hash: str = Query(..., min_length=64, max_length=64, description="SHA-256 hex hash to look up"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """
    Universal hash lookup — search both profile hashes and evidence hashes.
    Checks local DB and blockchain adapter.
    """
    records = []
    hash_type = "unknown"

    # Try profile hash
    profile_records = db.query(ProfileRecord).filter(ProfileRecord.profile_hash == hash).all()
    if profile_records:
        hash_type = "profile"
        for p in profile_records:
            records.append({
                "type": "ProfileRecord",
                "id": str(p.id),
                "platform": p.platform.value,
                "status": p.status.value,
                "risk_score": p.risk_score,
                "case_id": str(p.case_id),
                "created_at": p.created_at.isoformat(),
                "blockchain_tx_id": p.blockchain_tx_id,
            })

    # Try evidence hash
    evidence_records = db.query(EvidenceRecord).filter(EvidenceRecord.evidence_hash == hash).all()
    if evidence_records:
        hash_type = "evidence" if hash_type == "unknown" else "both"
        for e in evidence_records:
            records.append({
                "type": "EvidenceRecord",
                "id": str(e.id),
                "original_filename": e.original_filename,
                "evidence_type": e.evidence_type.value,
                "case_id": str(e.case_id),
                "created_at": e.created_at.isoformat(),
                "blockchain_tx_id": e.blockchain_tx_id,
            })

    # Cross-check blockchain (evidence)
    adapter = get_blockchain_adapter()
    chain_result = await adapter.verify_evidence_hash(hash)
    if chain_result["found"] and not evidence_records:
        hash_type = "evidence"
        records.append({"type": "BlockchainOnly", "metadata": chain_result["metadata"]})

    return RegistrySearchResult(
        hash=hash,
        hash_type=hash_type,
        found=bool(records),
        records=records,
    )


@router.get("/blacklist")
def get_flagged_profiles(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """Return all FLAGGED profiles — the blacklist registry."""
    from app.models import ProfileStatus
    flagged = (
        db.query(ProfileRecord)
        .filter(ProfileRecord.status == ProfileStatus.FLAGGED)
        .order_by(ProfileRecord.risk_score.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "profile_hash": p.profile_hash,
            "platform": p.platform.value,
            "risk_score": p.risk_score,
            "case_id": str(p.case_id),
            "created_at": p.created_at.isoformat(),
        }
        for p in flagged
    ]
