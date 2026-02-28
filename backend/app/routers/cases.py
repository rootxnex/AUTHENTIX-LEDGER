"""Cases router — CRUD for investigation cases."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_investigator_or_admin, require_any_role
from app.database import get_db
from app.models import Case, CaseStatus, EvidenceRecord, ProfileRecord, User
from app.schemas import CaseCreate, CaseUpdate, CaseOut, PaginatedResponse
from app.services.blockchain import get_blockchain_adapter

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=CaseOut, status_code=201)
async def create_case(
    body: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator_or_admin),
):
    case = Case(
        title=body.title,
        description=body.description,
        fir_number=body.fir_number,
        owner_unit=body.owner_unit,
        owner_id=current_user.id,
    )
    db.add(case)
    db.flush()  # get ID before blockchain call

    # Anchor on blockchain
    adapter = get_blockchain_adapter()
    tx_id = await adapter.create_case(
        case_id=str(case.id),
        title=body.title,
        owner_unit=body.owner_unit,
        created_by=str(current_user.id),
    )
    case.blockchain_tx_id = tx_id
    db.commit()
    db.refresh(case)

    out = CaseOut.model_validate(case)
    out.profile_count = 0
    out.evidence_count = 0
    return out


@router.get("", response_model=PaginatedResponse)
def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[CaseStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    query = db.query(Case)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    # Non-admin users see only their unit's cases
    if current_user.role.value not in ("ADMIN",) and current_user.unit:
        query = query.filter(Case.owner_unit == current_user.unit)
    total = query.count()
    cases = query.order_by(Case.created_at.desc()).offset((page - 1) * size).limit(size).all()

    items = []
    for c in cases:
        out = CaseOut.model_validate(c)
        out.profile_count = db.query(ProfileRecord).filter(ProfileRecord.case_id == c.id).count()
        out.evidence_count = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == c.id).count()
        items.append(out)

    import math
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=math.ceil(total / size))


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_any_role)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    out = CaseOut.model_validate(case)
    out.profile_count = db.query(ProfileRecord).filter(ProfileRecord.case_id == case_id).count()
    out.evidence_count = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == case_id).count()
    return out


@router.patch("/{case_id}", response_model=CaseOut)
async def update_case(
    case_id: uuid.UUID,
    body: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator_or_admin),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if body.title:
        case.title = body.title
    if body.description is not None:
        case.description = body.description
    if body.status:
        case.status = body.status
        adapter = get_blockchain_adapter()
        await adapter.update_case_status(str(case_id), body.status.value, str(current_user.id))

    db.commit()
    db.refresh(case)
    out = CaseOut.model_validate(case)
    out.profile_count = db.query(ProfileRecord).filter(ProfileRecord.case_id == case_id).count()
    out.evidence_count = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == case_id).count()
    return out
