"""Reports router — generate and download case PDFs."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_investigator_or_admin, require_any_role
from app.database import get_db
from app.models import Case, EvidenceRecord, ProfileRecord, User
from app.schemas import ReportRequest, ReportOut
from app.services.hashing import sha256_bytes
from app.services.report import generate_report_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportOut)
def generate_report(
    body: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator_or_admin),
):
    case = db.query(Case).filter(Case.id == body.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    profiles = db.query(ProfileRecord).filter(ProfileRecord.case_id == body.case_id).all()
    evidence = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == body.case_id).all()

    pdf_bytes = generate_report_pdf(
        case=case,
        profiles=profiles,
        evidence_records=evidence,
        investigator=current_user,
        investigator_notes=body.investigator_notes,
    )

    pdf_hash = sha256_bytes(pdf_bytes)
    report_id = f"RPT-{str(body.case_id)[:8].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Store PDF in MinIO for download
    from app.services.storage import upload_bytes
    storage_key = f"reports/{report_id}.pdf"
    upload_bytes(storage_key, pdf_bytes, content_type="application/pdf")

    return ReportOut(
        report_id=report_id,
        case_id=body.case_id,
        generated_at=datetime.now(timezone.utc),
        download_url=f"/reports/{report_id}/download",
        hash_proof=pdf_hash,
    )


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """Stream the PDF report for download."""
    from app.services.storage import download_bytes
    try:
        pdf_bytes = download_bytes(f"reports/{report_id}.pdf")
    except Exception:
        raise HTTPException(status_code=404, detail="Report not found or expired")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report_id}.pdf"'},
    )
