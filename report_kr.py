from __future__ import annotations
from typing import Dict, Any
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import inch

from common import risk_label_kr
from charts import make_7d_trend_png

_PDF_FONT = "HYSMyeongJo-Medium"
try:
    pdfmetrics.registerFont(UnicodeCIDFont(_PDF_FONT))
except Exception:
    pass

def _on_page_kr(canvas, doc, payload: Dict[str, Any]):
    meta = payload.get("meta", {})
    canvas.saveState()
    canvas.setFont(_PDF_FONT, 9)
    canvas.drawString(36, A4[1]-28, f"{meta.get('logo_text','Bio-OS')}  |  {meta.get('issuer','')}")
    canvas.setFont(_PDF_FONT, 8.5)
    canvas.drawRightString(A4[0]-36, A4[1]-28, f"문서번호 {meta.get('doc_id','-')}  ·  Rev. {meta.get('rev','-')}  ·  {meta.get('security_level','일반 공개')}")
    canvas.setFont(_PDF_FONT, 8.5)
    canvas.drawString(36, 22, "표준 운영 용어 기반 자동 생성 보고서")
    canvas.drawRightString(A4[0]-36, 22, f"{doc.page}")
    canvas.restoreState()

def make_pdf_kr(summary_only: bool, payload: Dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=36)

    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Heading1"], fontName=_PDF_FONT, fontSize=18, leading=22, spaceAfter=12)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=_PDF_FONT, fontSize=13, leading=17, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName=_PDF_FONT, fontSize=10.8, leading=15)

    meta = payload.get("meta", {})

    elements = []
    elements.append(Paragraph("Bio-OS 운영 보고서", title))
    elements.append(Paragraph(f"시설명: {meta.get('facility_name','-')}", body))
    elements.append(Paragraph(f"보고 기간: {meta.get('report_period','-')}", body))
    elements.append(Paragraph(f"작성/담당: {meta.get('report_owner','-')}", body))
    elements.append(Paragraph(f"시스템 버전: {meta.get('system_version','-')}", body))
    elements.append(Paragraph(f"생성 시각: {payload.get('generated_at','-')}", body))
    elements.append(Spacer(1, 0.15*inch))

    # 1) 요약
    elements.append(Paragraph("1. 전체 요약", h2))
    summary_tbl = Table([
        ["현재 상태", payload["status"]],
        ["전체 위험 점수(최대값 기준)", f"{payload['r_max']:.0f} / 100 (기준: {payload['culprit']})"],
        ["주요 원인", ", ".join(payload.get("causes_top_names", [c for c,_ in payload.get("causes", [])]))],
        ["지금 바로 조치", payload["p1"]],
    ], colWidths=[160, 340])
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

    # 2) 핵심 지표
    elements.append(Paragraph("2. 핵심 지표", h2))
    kpi_tbl = Table([
        ["갑작스런 변화(24시간)", f"{payload['shock_24h']} 회"],
        ["위험 노출 시간(7일)", f"{payload['exposure_7d_pct']:.0f}% (임시 환산)"],
        ["설비 사용률", f"{payload['util_pct']:.0f}% (임시)"],
        ["증설 판단 단계", payload["expansion_stage"]],
    ], colWidths=[160, 340])
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

    # 3) 근거
    elements.append(Paragraph("3. 근거(현재값/기준)", h2))
    ev = payload.get("evidence", [])
    if ev:
        for line in ev[:6]:
            elements.append(Paragraph(f"• {line}", body))
    else:
        elements.append(Paragraph("• (근거 데이터 없음)", body))

    # 4) 7일 추세 (요약에도 1개 포함)
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("4. 7일 추세(데모)", h2))
    png = make_7d_trend_png(payload["r_max"])
    img = Image(BytesIO(png), width=6.2*inch, height=2.6*inch)
    elements.append(img)

    if summary_only:
        doc.build(elements, onFirstPage=lambda c,d: _on_page_kr(c,d,payload), onLaterPages=lambda c,d: _on_page_kr(c,d,payload))
        return buf.getvalue()

    elements.append(PageBreak())

    # Page 2: 구역 비교
    elements.append(Paragraph("5. 구역(A/B) 비교", h2))
    la, lb = payload["loop_a"], payload["loop_b"]
    loop_tbl = Table([
        ["구역", "상태", "전체 위험 점수", "갑작스런 변화(24h)", "위험 노출(7일)", "설비 사용률"],
        ["A구역", risk_label_kr(float(la["risk"])), f"{float(la['risk']):.0f}", f"{int(la['shock_24h'])}", f"{float(la['exposure_7d'])*100:.0f}%", f"{float(la['util'])*100:.0f}%"],
        ["B구역", risk_label_kr(float(lb["risk"])), f"{float(lb['risk']):.0f}", f"{int(lb['shock_24h'])}", f"{float(lb['exposure_7d'])*100:.0f}%", f"{float(lb['util'])*100:.0f}%"],
    ], colWidths=[60, 70, 85, 95, 85, 85])
    loop_tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),_PDF_FONT),
        ("FONTSIZE",(0,0),(-1,-1),9.6),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CBD5E1")),
        ("ALIGN",(2,1),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    elements.append(loop_tbl)
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("6. 조치 계획", h2))
    elements.append(Paragraph("• 지금 바로 조치: " + payload["p1"], body))
    elements.append(Paragraph("• 오늘 안에 점검: (현장 점검 항목 기록)", body))
    elements.append(Paragraph("• 계획 수립 필요: (증설/개선 계획 수립)", body))

    elements.append(PageBreak())

    # Page 3: 제출용 섹션(정부/기관)
    elements.append(Paragraph("7. 사업 목적 및 기대효과(제출용)", h2))
    elements.append(Paragraph("• 목적: 수질·설비 상태를 하나의 ‘전체 위험 점수’로 통합하여, 사고를 사전에 감지하고 최소비용으로 운영 효율을 극대화한다.", body))
    elements.append(Paragraph("• 기대효과: (1) 사고 예방(조기 경고), (2) 운영 안정성 향상(노출 시간 감소), (3) 과잉투자 방지(증설 타이밍 객관화), (4) 표준화 기반 확보(용어·지표 체계).", body))

    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("8. 데이터 기반 의사결정 흐름(간단 도식)", h2))
    flow = Table([
        ["1) 수집", "센서/기록 데이터 수집(산소량·물 온도·pH·염도 등)"],
        ["2) 판단", "전체 위험 점수 산출 + 주요 원인 도출 + 갑작스런 변화 감지"],
        ["3) 조치", "지금 바로 조치 / 오늘 안에 점검 / 계획 수립 필요로 실행"],
        ["4) 검증", "위험 노출 시간/추세로 효과 확인(개선 여부)"],
        ["5) 확장", "설비 사용률·지표 기준으로 증설 판단 단계 결정"],
    ], colWidths=[80, 420])
    flow.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),_PDF_FONT),
        ("FONTSIZE",(0,0),(-1,-1),10.0),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#F2F4FF")),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CBD5E1")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    elements.append(flow)

    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("9. Seed-M1 → BioModule150 연결 전략(요약)", h2))
    elements.append(Paragraph("• Seed-M1: 위험 엔진(표준 용어/지표/조치 체계)을 먼저 검증하고, 운영 데이터·보고서 자동 생성 체계를 확립한다.", body))
    elements.append(Paragraph("• BioModule150: Seed-M1에서 검증된 위험 엔진을 모듈형 RAS 운영에 적용하여, 최소비용-최고효율 운영 및 증설 타이밍을 데이터로 결정한다.", body))
    elements.append(Paragraph("• 확장: 150평 모듈 성공 후 클러스터 형태로 확장(150→300→…); 동일 엔진/표준으로 다시설 운영이 가능하다.", body))

    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("10. 개정 이력", h2))
    rev_tbl = Table([
        ["Rev.", "개정 일자", "개정 내용"],
        [meta.get("rev","-"), meta.get("rev_date","-"), meta.get("rev_desc","-")]
    ], colWidths=[60, 120, 300])
    rev_tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),_PDF_FONT),
        ("FONTSIZE",(0,0),(-1,-1),9.6),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111827")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CBD5E1")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    elements.append(rev_tbl)

    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("11. 비고", h2))
    elements.append(Paragraph("본 보고서는 데모(샘플 데이터) 기반 자동 생성 예시이며, 실증 단계에서는 실제 센서/DB 값으로 자동 전환된다.", body))

    doc.build(elements, onFirstPage=lambda c,d: _on_page_kr(c,d,payload), onLaterPages=lambda c,d: _on_page_kr(c,d,payload))
    return buf.getvalue()
