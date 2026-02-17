from __future__ import annotations
from typing import Dict, Any
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

_PDF_FONT = "HYSMyeongJo-Medium"
try:
    pdfmetrics.registerFont(UnicodeCIDFont(_PDF_FONT))
except Exception:
    pass

def make_whitepaper_12p(payload: Dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=36)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontName=_PDF_FONT, fontSize=18, leading=22)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=_PDF_FONT, fontSize=13, leading=17)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName=_PDF_FONT, fontSize=10.8, leading=15)

    meta = payload.get("meta", {})
    elements = []
    elements.append(Paragraph("Bio-OS Global Standard Whitepaper", h1))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Facility: {meta.get('facility_name','-')} · Version: {meta.get('system_version','-')}", body))
    elements.append(Paragraph(f"Generated at: {payload.get('generated_at','-')}", body))
    elements.append(PageBreak())

    sections = [
        ("1. Executive Vision", "Bio-OS는 ‘최소비용-최고효율’ 운영을 데이터로 증명하는 운영 표준 체계다."),
        ("2. Problem Definition", "양식 운영 리스크는 ‘감지 지연’과 ‘과잉투자’가 동시에 발생한다."),
        ("3. Unified Risk Score", "전체 위험 점수는 수질/설비 상태를 0~100 단일 지표로 통합한다."),
        ("4. Decision Loop", "상태→원인→조치→검증→확장 의사결정 루프를 자동화한다."),
        ("5. Shock Detection", "갑작스런 변화를 조기 경고 신호로 감지하여 사고를 예방한다."),
        ("6. Exposure Model", "위험 노출 시간은 일시적 이상과 지속 위험을 구분한다."),
        ("7. Utilization & Scale", "설비 사용률 기반으로 증설 타이밍을 객관화한다."),
        ("8. Seed-M1 to BioModule150", "Seed-M1로 엔진을 검증하고 BioModule150에 적용해 모듈 확장을 구현한다."),
        ("9. Government Impact", "사고 예방, 운영 안정화, 표준화 기반 확보를 통한 공공 효과."),
        ("10. Global Standardization", "표준 용어/지표/보고서 체계를 글로벌 이해관계자에 맞게 확장한다."),
        ("11. Deployment Model", "클라우드 콘솔 + 현장 센서/DB 연동으로 단계적 확장이 가능하다."),
        ("12. Future Expansion", "다종 생물/다산업으로 확장 가능한 Bio-OS 아키텍처."),
    ]
    for title, desc in sections:
        elements.append(Paragraph(title, h2))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(desc, body))
        elements.append(PageBreak())

    doc.build(elements)
    return buf.getvalue()
