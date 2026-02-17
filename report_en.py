from __future__ import annotations
from typing import Dict, Any
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import inch

from common import risk_label_en

_PDF_FONT = "HYSMyeongJo-Medium"
try:
    pdfmetrics.registerFont(UnicodeCIDFont(_PDF_FONT))
except Exception:
    pass

def _on_page_en(canvas, doc, payload: Dict[str, Any]):
    meta = payload.get("meta", {})
    canvas.saveState()
    canvas.setFont(_PDF_FONT, 9)
    canvas.drawString(36, A4[1]-28, f"{meta.get('logo_text','Bio-OS')}  |  {meta.get('issuer','')}")
    canvas.setFont(_PDF_FONT, 8.5)
    canvas.drawRightString(A4[0]-36, A4[1]-28, f"Doc {meta.get('doc_id','-')}  ·  Rev. {meta.get('rev','-')}  ·  {meta.get('security_level','Public')}")
    canvas.setFont(_PDF_FONT, 8.5)
    canvas.drawString(36, 22, "Auto-generated report (standard terminology)")
    canvas.drawRightString(A4[0]-36, 22, f"{doc.page}")
    canvas.restoreState()

def make_pdf_en(summary_only: bool, payload: Dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=36)

    styles = getSampleStyleSheet()
    title = ParagraphStyle("title_en", parent=styles["Heading1"], fontName=_PDF_FONT, fontSize=18, leading=22, spaceAfter=12)
    h2 = ParagraphStyle("h2_en", parent=styles["Heading2"], fontName=_PDF_FONT, fontSize=13, leading=17, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body_en", parent=styles["BodyText"], fontName=_PDF_FONT, fontSize=10.8, leading=15)

    meta = payload.get("meta", {})

    elements = []
    elements.append(Paragraph("Bio-OS Operations Report", title))
    elements.append(Paragraph(f"Facility: {meta.get('facility_name','-')}", body))
    elements.append(Paragraph(f"Period: {meta.get('report_period','-')}", body))
    elements.append(Paragraph(f"Owner: {meta.get('report_owner','-')}", body))
    elements.append(Paragraph(f"System Version: {meta.get('system_version','-')}", body))
    elements.append(Paragraph(f"Generated at: {payload.get('generated_at','-')}", body))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("1. Executive Summary", h2))
    summary_tbl = Table([
        ["Status", risk_label_en(float(payload["r_max"]))],
        ["Global Risk Score (max)", f"{payload['r_max']:.0f} / 100 (Reference: {payload['culprit']})"],
        ["Top Drivers", ", ".join(payload["causes"])],
        ["Immediate Action", payload["p1"]],
    ], colWidths=[170, 330])
    summary_tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),_PDF_FONT),
        ("FONTSIZE",(0,0),(-1,-1),10.5),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#F2F4FF")),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CBD5E1")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    elements.append(summary_tbl)
    elements.append(Spacer(1, 0.18*inch))

    elements.append(Paragraph("2. Key Metrics", h2))
    kpi_tbl = Table([
        ["Shock Events (24h)", f"{payload['shock_24h']}"],
        ["Risk Exposure (7d)", f"{payload['exposure_7d_pct']:.0f}% (proxy)"],
        ["Facility Utilization", f"{payload['util_pct']:.0f}% (demo)"],
        ["Scale Decision Stage", payload["expansion_stage"]],
    ], colWidths=[170, 330])
    kpi_tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),_PDF_FONT),
        ("FONTSIZE",(0,0),(-1,-1),10.5),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#F7F7F7")),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CBD5E1")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    elements.append(kpi_tbl)

    elements.append(Spacer(1, 0.18*inch))
    elements.append(Paragraph("3. Evidence (current vs reference)", h2))
    ev = payload.get("evidence", [])
    if ev:
        for line in ev[:6]:
            elements.append(Paragraph(f"• {line}", body))
    else:
        elements.append(Paragraph("• (No evidence data)", body))

    if summary_only:
        doc.build(elements, onFirstPage=lambda c,d: _on_page_en(c,d,payload), onLaterPages=lambda c,d: _on_page_en(c,d,payload))
        return buf.getvalue()

    elements.append(PageBreak())
    elements.append(Paragraph("4. Glossary (Standard Terms)", h2))
    gloss = Table([
        ["Korean (UI)", "English (Global)", "Meaning"],
        ["전체 위험 점수", "Global Risk Score", "Unified risk score (0–100)"],
        ["갑작스런 변화", "Shock Event", "Rapid change detected"],
        ["위험 노출 시간", "Risk Exposure Time", "Time/proxy share outside normal band"],
        ["설비 사용률", "Facility Utilization", "Usage level of capacity"],
        ["증설 판단 단계", "Scale Decision Stage", "Stage for scale-out decision"],
        ["지금 바로 조치", "Immediate Action", "Execute now"],
        ["오늘 안에 점검", "Check Today", "Inspect within 24 hours"],
        ["계획 수립 필요", "Plan Required", "Prepare improvement/scale plan"],
    ], colWidths=[140, 160, 200])
    gloss.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),_PDF_FONT),
        ("FONTSIZE",(0,0),(-1,-1),9.6),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CBD5E1")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    elements.append(gloss)

    elements.append(Spacer(1, 0.18*inch))
    elements.append(Paragraph("5. Standardization Note", h2))
    elements.append(Paragraph("Korean UI terminology is standardized for field operations; this English report is provided for global dissemination.", body))

    doc.build(elements, onFirstPage=lambda c,d: _on_page_en(c,d,payload), onLaterPages=lambda c,d: _on_page_en(c,d,payload))
    return buf.getvalue()
