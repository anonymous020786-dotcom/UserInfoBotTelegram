import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from config import EXPORTS_DIR


def generate_osint_pdf(
    entity_id: int,
    title: str,
    username: Optional[str],
    entity_type: str,
    reg_estimate: str,
    dc_info: str,
    bio: Optional[str],
    extra_details: Dict[str, Any]
) -> Path:
    """
    Generates a PDF OSINT Intelligence Dossier using ReportLab.
    """
    pdf_path = EXPORTS_DIR / f"dossier_{entity_id}_{abs(hash(title)) % 10000}.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subheader_style = ParagraphStyle(
        'SubheaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155'),
        leading=13
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("SENTINEL OSINT INTELLIGENCE REPORT", header_style))
    story.append(Paragraph(f"Document ID: SEN-{abs(hash(str(entity_id))):X} &bull; Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} &bull; Status: VERIFIED", subheader_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=15))

    # Core Entity Profile Table
    story.append(Paragraph("1. TARGET PROFILE SUMMARY", section_title))
    
    table_data = [
        [Paragraph("<b>Attribute</b>", body_style), Paragraph("<b>Value / Assessment</b>", body_style)],
        [Paragraph("Telegram ID", body_style), Paragraph(str(entity_id), body_style)],
        [Paragraph("Name / Title", body_style), Paragraph(title or "N/A", body_style)],
        [Paragraph("Username", body_style), Paragraph(f"@{username}" if username else "None", body_style)],
        [Paragraph("Entity Type", body_style), Paragraph(entity_type.capitalize(), body_style)],
        [Paragraph("Registration Estimate", body_style), Paragraph(reg_estimate, body_style)],
        [Paragraph("Data Center (DC)", body_style), Paragraph(dc_info, body_style)],
        [Paragraph("Premium Status", body_style), Paragraph("True (Telegram Premium)" if extra_details.get("is_premium") else "Standard Account", body_style)],
        [Paragraph("Official Verification", body_style), Paragraph("Verified by Telegram" if extra_details.get("is_verified") else "Unverified", body_style)],
        [Paragraph("Scam / Fake Flags", body_style), Paragraph("FLAGGED SCAM" if extra_details.get("is_scam") else "Clean / No Flags Reported", body_style)],
    ]

    t = Table(table_data, colWidths=[2.2 * inch, 5.0 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Biography / Description
    story.append(Paragraph("2. BIOGRAPHY & DESCRIPTION", section_title))
    bio_text = bio if bio else "No biography or description provided by the entity."
    story.append(Paragraph(bio_text.replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 15))

    # Extended Security & OSINT Analysis
    story.append(Paragraph("3. OSINT AUDIT & RECONNAISSANCE", section_title))
    recon_rows = [
        [Paragraph("<b>Recon Check</b>", body_style), Paragraph("<b>Observation</b>", body_style)],
        [Paragraph("Permanent Direct Link", body_style), Paragraph(f"tg://user?id={entity_id}", body_style)],
        [Paragraph("Web Resolve URL", body_style), Paragraph(f"https://t.me/{username}" if username else "N/A", body_style)],
        [Paragraph("Extracted Links / Domains", body_style), Paragraph(", ".join(extra_details.get("links", [])) or "None detected", body_style)],
        [Paragraph("Extracted Mentions", body_style), Paragraph(", ".join(extra_details.get("mentions", [])) or "None detected", body_style)],
        [Paragraph("Detected Script / Language", body_style), Paragraph(extra_details.get("language_script", "Standard Latin / Universal"), body_style)],
    ]
    t2 = Table(recon_rows, colWidths=[2.2 * inch, 5.0 * inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t2)
    story.append(Spacer(1, 20))

    # Disclaimer Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#94a3b8'), spaceAfter=8))
    story.append(Paragraph(
        "<i>Disclaimer: This document is automatically generated by Sentinel Bot for identification and OSINT verification purposes based on public Telegram metadata.</i>",
        ParagraphStyle('FooterDisclaimer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#94a3b8'))
    ))

    doc.build(story)
    return pdf_path
