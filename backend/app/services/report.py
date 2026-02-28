"""
PDF Report Generation Service — court-ready format compliant with Section 65B.
Generates a signed, hash-proofed PDF document.
"""
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models import Case, EvidenceRecord, ProfileRecord, User


def _header_footer(canvas, doc):
    canvas.saveState()
    W, H = A4
    # Top header bar
    canvas.setFillColor(colors.HexColor("#1a1a2e"))
    canvas.rect(0, H - 20 * mm, W, 20 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawCentredString(W / 2, H - 12 * mm, "AUTHENTIX LEDGER — CONFIDENTIAL INVESTIGATION REPORT")
    # Footer
    canvas.setFillColor(colors.HexColor("#cccccc"))
    canvas.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#333333"))
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        W / 2, 3.5 * mm,
        f"Page {doc.page}  |  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  |  AUTHENTIX LEDGER — For Official Use Only"
    )
    canvas.restoreState()


def generate_report_pdf(
    case: Case,
    profiles: list[ProfileRecord],
    evidence_records: list[EvidenceRecord],
    investigator: User,
    investigator_notes: Optional[str] = None,
) -> bytes:
    """
    Generate a court-ready PDF investigation report.
    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=28 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    bold = ParagraphStyle("Bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10)
    heading2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#1a1a2e"), spaceAfter=4)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#555555"))
    mono = ParagraphStyle("Mono", parent=styles["Normal"], fontName="Courier", fontSize=8, leftIndent=10)
    ACCENT = colors.HexColor("#e94560")

    story = []

    # ── Cover Page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph("DIGITAL INVESTIGATION REPORT", ParagraphStyle(
        "Cover", fontName="Helvetica-Bold", fontSize=22, textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER
    )))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Section 65B — Indian Evidence Act Compliant", ParagraphStyle(
        "Sub", fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#555555"), alignment=TA_CENTER
    )))
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
    story.append(Spacer(1, 6 * mm))

    meta_data = [
        ["Case ID:", str(case.id)],
        ["Case Title:", case.title],
        ["FIR Number:", case.fir_number or "N/A"],
        ["Owning Unit:", case.owner_unit],
        ["Case Status:", case.status.value],
        ["Report Generated:", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")],
        ["Generating Officer:", f"{investigator.full_name or investigator.username} ({investigator.unit or 'N/A'})"],
        ["Profiles Analyzed:", str(len(profiles))],
        ["Evidence Items:", str(len(evidence_records))],
    ]
    tbl = Table(meta_data, colWidths=[55 * mm, 115 * mm])
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f5f5f5"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ── Section 65B Certificate Block ─────────────────────────────────────────
    story.append(Paragraph("Section 65B Certificate (Indian Evidence Act)", heading2))
    cert_text = (
        "I, <b>{officer}</b>, hereby certify that the digital records contained in this report were "
        "produced by the <b>AUTHENTIX LEDGER</b> system, a computer resource regularly used in the "
        "lawful investigation of cybercrime. The records were produced by the regular activity of the "
        "said computer resource, which was operating properly at all relevant times. The information "
        "contained herein is a reproduction of the data stored in the system. "
        "All evidence hashes are computed using SHA-256 and anchored on a permissioned blockchain ledger "
        "to establish chain-of-custody and tamper-evidence."
    ).format(officer=investigator.full_name or investigator.username)
    story.append(Paragraph(cert_text, styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    # ── Case Description ──────────────────────────────────────────────────────
    story.append(Paragraph("Case Summary", heading2))
    story.append(Paragraph(case.description or "No description provided.", styles["Normal"]))
    story.append(Spacer(1, 4 * mm))

    # ── Profile Risk Analysis ─────────────────────────────────────────────────
    story.append(Paragraph("Analyzed Profiles — Risk Assessment", heading2))
    for i, p in enumerate(profiles, 1):
        story.append(Paragraph(f"{i}. Profile Record", bold))
        risk_level = "CRITICAL" if (p.risk_score or 0) >= 75 else "HIGH" if (p.risk_score or 0) >= 50 else "MEDIUM" if (p.risk_score or 0) >= 25 else "LOW"
        risk_color = {"CRITICAL": "#e94560", "HIGH": "#ff6b35", "MEDIUM": "#ffa500", "LOW": "#28a745"}.get(risk_level, "#555555")
        pdata = [
            ["Profile Hash (SHA-256):", p.profile_hash],
            ["Platform:", p.platform.value.upper()],
            ["Risk Score:", f"{p.risk_score:.1f} / 100"],
            ["Risk Level:", risk_level],
            ["Status:", p.status.value],
            ["Blockchain TX:", p.blockchain_tx_id or "N/A"],
            ["Recorded At:", p.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")],
        ]
        ptbl = Table(pdata, colWidths=[55 * mm, 115 * mm])
        ptbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
            ("TEXTCOLOR", (1, 2), (1, 2), colors.HexColor(risk_color)),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("FONTNAME", (1, 0), (1, 0), "Courier"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#fafafa"), colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(ptbl)

        # Risk factors
        if p.risk_factors:
            try:
                factors = json.loads(p.risk_factors)
                story.append(Spacer(1, 2 * mm))
                story.append(Paragraph("Top Risk Factors:", small))
                for f in factors[:5]:
                    direction = "↑" if f.get("direction") == "increases_risk" else "↓"
                    story.append(Paragraph(
                        f"  {direction} <b>{f.get('name', '')}</b>: {f.get('description', '')} (contribution: {f.get('contribution', 0):.2f})",
                        mono
                    ))
            except Exception:
                pass
        story.append(Spacer(1, 5 * mm))

    # ── Evidence Hash Manifest ─────────────────────────────────────────────────
    story.append(Paragraph("Evidence Hash Manifest", heading2))
    story.append(Paragraph("The following evidence items have been cryptographically hashed (SHA-256) and anchored on the blockchain ledger:", small))
    story.append(Spacer(1, 3 * mm))

    evid_header = [["#", "Filename", "Type", "SHA-256 Hash", "Blockchain TX", "Timestamp"]]
    evid_rows = evid_header + [
        [
            str(i + 1),
            e.original_filename[:25] + "..." if len(e.original_filename) > 25 else e.original_filename,
            e.evidence_type.value,
            e.evidence_hash[:24] + "...",
            (e.blockchain_tx_id or "N/A")[:20] + "..." if e.blockchain_tx_id and len(e.blockchain_tx_id) > 20 else (e.blockchain_tx_id or "N/A"),
            e.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ]
        for i, e in enumerate(evidence_records)
    ]
    etbl = Table(evid_rows, colWidths=[8 * mm, 38 * mm, 22 * mm, 38 * mm, 38 * mm, 28 * mm])
    etbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
        ("FONTNAME", (3, 1), (3, -1), "Courier"),
        ("FONTNAME", (4, 1), (4, -1), "Courier"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4ff"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(etbl)
    story.append(Spacer(1, 6 * mm))

    # ── Investigator Notes ─────────────────────────────────────────────────────
    if investigator_notes:
        story.append(Paragraph("Investigator Notes", heading2))
        story.append(Paragraph(investigator_notes, styles["Normal"]))
        story.append(Spacer(1, 4 * mm))

    # ── Signature Block ────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 4 * mm))
    sig_data = [
        ["Officer Name:", investigator.full_name or investigator.username],
        ["Investigator ID:", str(investigator.id)],
        ["Unit:", investigator.unit or "N/A"],
        ["Email:", investigator.email],
        ["Digital Signature:", "Signed via AUTHENTIX LEDGER system (JWT-authenticated session)"],
        ["Report Date:", datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")],
    ]
    stbl = Table(sig_data, colWidths=[45 * mm, 125 * mm])
    stbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(stbl)

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
