import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from io import BytesIO
# PDF 보고서 생성(표준 한글)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import inch

st.set_page_config(page_title="Bio-OS Premium Console", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
:root{
  --bg0:#070A12;
  --bg1:#0B1020;
  --bg2:#0E1630;
  --stroke:#1C2A55;
  --strokeStrong:#2A57FF;
  --text:#E9EEFF;
  --muted:#AAB5E8;
  --ok:#3FE38E;
  --warn:#FFB020;
  --risk:#FF4D4D;
  --teal:#1BE7FF;
  --purple:#B28DFF;
  --gray:#93A4B7;
}
html, body, [class*="css"]{ background: var(--bg0); color: var(--text); }
section.main > div { padding-top: 0.8rem; }
.small-muted { color: var(--muted); font-size: 0.9rem; }
.kpi-big { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; }
.kpi-sub { color: var(--muted); font-size: 0.95rem; margin-top: -0.2rem; }

.zone{
  border: 1px solid var(--stroke);
  border-radius: 16px;
  padding: 14px 14px 10px 14px;
  background: linear-gradient(180deg, rgba(14,22,48,0.82), rgba(11,16,32,0.82));
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  margin-bottom: 14px;
}
.zone-strong{
  border: 2px solid rgba(42,87,255,0.75);
  background: radial-gradient(1100px 260px at 18% 0%, rgba(42,87,255,0.25), rgba(0,0,0,0)) , linear-gradient(180deg, rgba(14,22,48,0.86), rgba(11,16,32,0.86));
}
.zone-titlebar{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 12px;
}
.zone-title{
  font-weight: 800;
  letter-spacing: 0.03em;
  font-size: 0.92rem;
  text-transform: uppercase;
}
.badge{
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.85rem;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.04);
}
.badge-ok { color: var(--ok); border-color: rgba(63,227,142,0.35); background: rgba(63,227,142,0.10); }
.badge-warn { color: var(--warn); border-color: rgba(255,176,32,0.35); background: rgba(255,176,32,0.10); }
.badge-risk { color: var(--risk); border-color: rgba(255,77,77,0.35); background: rgba(255,77,77,0.10); }

.card{
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 12px;
  background: rgba(255,255,255,0.03);
}
.card-title{
  color: var(--muted);
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 6px;
}
.pill{
  display:inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.04);
  font-size: 0.80rem;
  color: var(--muted);
}
.p1 { color: var(--risk); border-color: rgba(255,77,77,0.35); background: rgba(255,77,77,0.10); }
.p2 { color: var(--warn); border-color: rgba(255,176,32,0.35); background: rgba(255,176,32,0.10); }
.p3 { color: var(--teal); border-color: rgba(27,231,255,0.35); background: rgba(27,231,255,0.10); }
.hr{ height: 1px; background: rgba(255,255,255,0.08); margin: 10px 0; }
.metric-grid{ display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; }
@media (max-width: 1200px){ .metric-grid{ grid-template-columns: 1fr 1fr; } }
.note{ color: var(--muted); font-size: 0.9rem; line-height: 1.35; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------
# PDF 보고서 생성 (1페이지 요약 / 3페이지 상세)
# - 화면 표준 한글 용어 그대로 사용
# -----------------------------
_PDF_FONT = "HYSMyeongJo-Medium"
try:
    pdfmetrics.registerFont(UnicodeCIDFont(_PDF_FONT))
except Exception:
    pass

def _risk_label(score: float) -> str:
    if score < 40: return "정상"
    if score < 60: return "주의"
    if score < 75: return "경계"
    return "위험"

def build_report_payload(m: dict, facility_name: str, report_period: str, report_owner: str, system_version: str, doc_id: str, rev: str, issuer: str, logo_text: str, rev_date: str, rev_desc: str) -> dict:
    r_max = float(max(m["loop_a"]["risk"], m["loop_b"]["risk"]))
    culprit = "A구역" if m["loop_a"]["risk"] >= m["loop_b"]["risk"] else "B구역"
    status = _risk_label(r_max)

    causes = [c for c, _ in m.get("causes", [])][:3] or ["특이 이상 없음"]
    actions = m.get("actions", [])
    p1 = actions[0][1] if actions else "운영 조건 점검"

    shock = int(m["loop_a"]["shock_24h"] + m["loop_b"]["shock_24h"])
    exposure = max(m["loop_a"]["exposure_7d"], m["loop_b"]["exposure_7d"])
    util = max(m["loop_a"]["util"], m["loop_b"]["util"])

    if r_max >= 75:
        expansion_stage = "즉시 증설 검토"
    elif r_max >= 60:
        expansion_stage = "설비 증설 준비"
    elif r_max >= 40:
        expansion_stage = "운영 조정 필요"
    else:
        expansion_stage = "설비 여유 있음"

    return {
        "facility_name": facility_name,
        "report_period": report_period,
        "report_owner": report_owner,
        "system_version": system_version,
        "doc_id": doc_id,
        "rev": rev,
        "issuer": issuer,
        "logo_text": logo_text,
        "rev_date": rev_date,
        "rev_desc": rev_desc,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "r_max": r_max,
        "culprit": culprit,
        "causes": causes,
        "p1": p1,
        "shock_24h": shock,
        "exposure_7d_pct": float(exposure) * 100.0,
        "util_pct": float(util) * 100.0,
        "expansion_stage": expansion_stage,
        "evidence": m.get("evidence", []),
        "loop_a": m["loop_a"],
        "loop_b": m["loop_b"],
    }

def make_pdf(summary_only: bool, payload: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=36)

    def _on_page(canvas, doc_):
        canvas.saveState()
        canvas.setFont(_PDF_FONT, 9)
        # Header (text logo + issuer)
        canvas.drawString(36, A4[1]-28, f"{payload.get('logo_text','Bio-OS')}  |  {payload.get('issuer','')}")
        canvas.setFont(_PDF_FONT, 8.5)
        canvas.drawRightString(A4[0]-36, A4[1]-28, f"문서번호 {payload.get('doc_id','-')}  ·  Rev. {payload.get('rev','-')}")
        # Footer
        canvas.setFont(_PDF_FONT, 8.5)
        canvas.drawString(36, 22, "표준 운영 용어 기반 자동 생성 보고서")
        canvas.drawRightString(A4[0]-36, 22, f"{doc_.page}")
        canvas.restoreState()

    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Heading1"], fontName=_PDF_FONT, fontSize=18, leading=22, spaceAfter=12)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=_PDF_FONT, fontSize=13, leading=17, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName=_PDF_FONT, fontSize=10.8, leading=15)

    elements = []
    elements.append(Paragraph("Bio-OS 운영 보고서", title))
    elements.append(Paragraph(f"시설명: {payload.get('facility_name', '-')}", body))
    elements.append(Paragraph(f"보고 기간: {payload.get('report_period', '-')}", body))
    elements.append(Paragraph(f"작성/담당: {payload.get('report_owner', '-')}", body))
    elements.append(Paragraph(f"시스템 버전: {payload.get('system_version', '-')}", body))
    elements.append(Paragraph(f"생성 시각: {payload['generated_at']}", body))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("1. 전체 요약", h2))
    summary_tbl = Table([
        ["현재 상태", payload["status"]],
        ["전체 위험 점수(최대값 기준)", f"{payload['r_max']:.0f} / 100 (기준: {payload['culprit']})"],
        ["주요 원인", ", ".join(payload["causes"])],
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

    elements.append(Paragraph("3. 근거(현재값/기준)", h2))
    if payload["evidence"]:
        for line in payload["evidence"][:6]:
            elements.append(Paragraph(f"• {line}", body))
    else:
        elements.append(Paragraph("• (근거 데이터 없음)", body))

    if summary_only:
        doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)
        return buf.getvalue()

    elements.append(PageBreak())

    elements.append(Paragraph("4. 구역(A/B) 비교", h2))
    la, lb = payload["loop_a"], payload["loop_b"]
    loop_tbl = Table([
        ["구역", "상태", "전체 위험 점수", "갑작스런 변화(24h)", "위험 노출(7일)", "설비 사용률"],
        ["A구역", _risk_label(float(la["risk"])), f"{float(la['risk']):.0f}", f"{int(la['shock_24h'])}", f"{float(la['exposure_7d'])*100:.0f}%", f"{float(la['util'])*100:.0f}%"],
        ["B구역", _risk_label(float(lb["risk"])), f"{float(lb['risk']):.0f}", f"{int(lb['shock_24h'])}", f"{float(lb['exposure_7d'])*100:.0f}%", f"{float(lb['util'])*100:.0f}%"],
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

    elements.append(Paragraph("5. 조치 계획", h2))
    elements.append(Paragraph("• 지금 바로 조치: " + payload["p1"], body))
    elements.append(Paragraph("• 오늘 안에 점검: (현장 점검 항목 기록)", body))
    elements.append(Paragraph("• 계획 수립 필요: (증설/개선 계획 수립)", body))

    elements.append(PageBreak())

    elements.append(Paragraph("6. 운영 판단 원칙(제출용 요약)", h2))
    principles = [
        "전체 위험 점수는 가장 위험한 구역 기준으로 판단한다.",
        "갑작스런 변화는 사고 이전의 조기 경고 신호로 간주한다.",
        "위험 노출 시간이 증가하면 운영 조정 또는 설비 증설을 검토한다.",
        "설비 사용률이 높게 지속되면 증설 판단 단계가 상향된다.",
        "모든 표기는 표준 한글 용어를 사용한다.",
    ]
    for p in principles:
        elements.append(Paragraph(f"• {p}", body))

    elements.append(Spacer(1, 0.2*inch))

    # 정부/기관 제출용 고정 설명(표준 문구)
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("6-1. 사업 목적 및 기대효과(제출용)", h2))
    elements.append(Paragraph("• 목적: 수질·설비 상태를 하나의 ‘전체 위험 점수’로 통합하여, 사고를 사전에 감지하고 최소비용으로 운영 효율을 극대화한다.", body))
    elements.append(Paragraph("• 기대효과: (1) 사고 예방(조기 경고), (2) 운영 안정성 향상(노출 시간 감소), (3) 과잉투자 방지(증설 타이밍 객관화), (4) 표준화 기반 확보(용어·지표 체계).", body))

    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("6-2. 데이터 기반 의사결정 흐름(간단 도식)", h2))
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
    
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("6-3. 개정 이력", h2))
    rev_tbl = Table([
        ["Rev.", "개정 일자", "개정 내용"],
        [payload.get("rev","-"), payload.get("rev_date","-"), payload.get("rev_desc","-")]
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
elements.append(Paragraph("7. 비고", h2))
    elements.append(Paragraph("본 보고서는 데모(샘플 데이터) 기반 자동 생성 예시이며, 실증 단계에서는 실제 센서/DB 값으로 자동 전환된다.", body))

    doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

# -----------------------------
# Global (English) Report Generator
# - Separate from Korean UI, for global standardization
# -----------------------------
def _risk_label_en(score: float) -> str:
    if score < 40: return "Normal"
    if score < 60: return "Caution"
    if score < 75: return "Watch"
    return "Critical"

def make_pdf_en(summary_only: bool, payload: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=36)

    def _on_page_en(canvas, doc_):
        canvas.saveState()
        canvas.setFont(_PDF_FONT, 9)
        canvas.drawString(36, A4[1]-28, f"{payload.get('logo_text','Bio-OS')}  |  {payload.get('issuer','')}")
        canvas.setFont(_PDF_FONT, 8.5)
        canvas.drawRightString(A4[0]-36, A4[1]-28, f"Doc {payload.get('doc_id','-')}  ·  Rev. {payload.get('rev','-')}")
        canvas.setFont(_PDF_FONT, 8.5)
        canvas.drawString(36, 22, "Auto-generated report (standard terminology)")
        canvas.drawRightString(A4[0]-36, 22, f"{doc_.page}")
        canvas.restoreState()

    styles = getSampleStyleSheet()
    title = ParagraphStyle("title_en", parent=styles["Heading1"], fontName=_PDF_FONT, fontSize=18, leading=22, spaceAfter=12)
    h2 = ParagraphStyle("h2_en", parent=styles["Heading2"], fontName=_PDF_FONT, fontSize=13, leading=17, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body_en", parent=styles["BodyText"], fontName=_PDF_FONT, fontSize=10.8, leading=15)

    elements = []
    elements.append(Paragraph("Bio-OS Operations Report", title))
    elements.append(Paragraph(f"Facility: {payload.get('facility_name','-')}", body))
    elements.append(Paragraph(f"Period: {payload.get('report_period','-')}", body))
    elements.append(Paragraph(f"Owner: {payload.get('report_owner','-')}", body))
    elements.append(Paragraph(f"System Version: {payload.get('system_version','-')}", body))
    elements.append(Paragraph(f"Generated at: {payload.get('generated_at','-')}", body))
    elements.append(Spacer(1, 0.15*inch))

    # Summary
    elements.append(Paragraph("1. Executive Summary", h2))
    summary_tbl = Table([
        ["Status", _risk_label_en(float(payload["r_max"]))],
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
    elements.append(Paragraph("3. Evidence (current vs. reference)", h2))
    if payload.get("evidence"):
        for line in payload["evidence"][:6]:
            elements.append(Paragraph(f"• {line}", body))
    else:
        elements.append(Paragraph("• (No evidence data)", body))

    if summary_only:
        doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)
        return buf.getvalue()

    elements.append(PageBreak())
    elements.append(Paragraph("4. Zone Comparison (A/B)", h2))
    la, lb = payload["loop_a"], payload["loop_b"]
    loop_tbl = Table([
        ["Zone", "Status", "Risk", "Shocks(24h)", "Exposure(7d)", "Utilization"],
        ["Zone A", _risk_label_en(float(la["risk"])), f"{float(la['risk']):.0f}", f"{int(la['shock_24h'])}", f"{float(la['exposure_7d'])*100:.0f}%", f"{float(la['util'])*100:.0f}%"],
        ["Zone B", _risk_label_en(float(lb["risk"])), f"{float(lb['risk']):.0f}", f"{int(lb['shock_24h'])}", f"{float(lb['exposure_7d'])*100:.0f}%", f"{float(lb['util'])*100:.0f}%"],
    ], colWidths=[70, 70, 70, 90, 95, 75])
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

    elements.append(PageBreak())
    elements.append(Paragraph("5. Glossary (Standard Terms)", h2))
gloss = Table([
    ["Korean (UI)", "English (Global)", "Meaning"],
    ["전체 위험 점수", "Global Risk Score", "Unified risk score (0–100)"],
    ["갑작스런 변화", "Shock Event", "Rapid change detected within short time window"],
    ["위험 노출 시간", "Risk Exposure Time", "Time/proxy share spent outside normal band"],
    ["설비 사용률", "Facility Utilization", "Usage level of oxygen/pump/filtration capacity"],
    ["증설 판단 단계", "Scale Decision Stage", "Stage for scale-out (prepare / review)"],
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
    ("LEFTPADDING",(0,0),(-1,-1),6),
    ("RIGHTPADDING",(0,0),(-1,-1),6),
]))
elements.append(gloss)
elements.append(Spacer(1, 0.18*inch))
elements.append(Paragraph("6. Standardization Note", h2))
elements.append(Paragraph("Korean UI terminology is standardized for field operations; this English report is provided for global dissemination and cross-border stakeholders.", body))
doc.build(elements)
return buf.getvalue()

def risk_label(score: float) -> str:
    if score < 40: return "정상"
    if score < 60: return "주의"
    if score < 75: return "경계"
    return "위험"

def risk_badge_class(score: float) -> str:
    if score < 40: return "badge badge-ok"
    if score < 60: return "badge badge-warn"
    return "badge badge-risk"

@st.cache_data(ttl=5)
def load_latest_metrics(scenario: str = '일반'):
    loop_a = dict(risk=68, shock_24h=4, exposure_7d=0.32, util=0.86, do=6.2, temp=16.8, ph=7.72, sal=31.2)
    loop_b = dict(risk=31, shock_24h=0, exposure_7d=0.06, util=0.40, do=7.6, temp=16.6, ph=7.92, sal=31.0)

    # 데모 시나리오(샘플 데이터) 프리셋
    # - 내부 로직/파라미터는 건드리지 않고, 화면 데모용 값만 변경
    if scenario == "산소량 급락":
        loop_a.update(dict(risk=82, shock_24h=9, exposure_7d=0.48, util=0.92, do=5.3, temp=16.8, ph=7.68, sal=31.2))
        loop_b.update(dict(risk=34, shock_24h=0, exposure_7d=0.05, util=0.38, do=7.7, temp=16.6, ph=7.92, sal=31.0))
    elif scenario == "물 흐름 저하":
        loop_a.update(dict(risk=63, shock_24h=2, exposure_7d=0.28, util=0.88, do=6.6, temp=16.7, ph=7.74, sal=31.1))
        loop_b.update(dict(risk=41, shock_24h=1, exposure_7d=0.12, util=0.62, do=7.2, temp=16.6, ph=7.88, sal=31.0))
    elif scenario == "여과 부담 증가":
        loop_a.update(dict(risk=58, shock_24h=1, exposure_7d=0.22, util=0.84, do=6.9, temp=16.8, ph=7.55, sal=31.2))
        loop_b.update(dict(risk=46, shock_24h=0, exposure_7d=0.15, util=0.66, do=7.4, temp=16.6, ph=7.83, sal=31.0))
    r_max = max(loop_a["risk"], loop_b["risk"])
    culprit = "Loop A" if loop_a["risk"] >= loop_b["risk"] else "Loop B"
    causes = [("산소 출렁임 증가", "DO 변동성 증가"), ("물순환 약화", "순환 상태 저하"), ("여과 부담 증가", "pH 불안정/부하 증가")]
    actions = [("P1", "산소 공급 단계 상향", "즉시"), ("P2", "여과 세척 주기 단축", "오늘"), ("P3", "생물여과 미디어 20% 추가 준비", "계획")]
    expansion_stage = "증설 준비 단계" if r_max >= 60 else "정상"
    evidence = [
        f"산소(Loop A) {loop_a['do']:.1f} (기준 6.0~10.0)",
        f"pH(Loop A) {loop_a['ph']:.2f} (기준 7.6~8.3)",
        f"설비 사용률(Loop A) {loop_a['util']*100:.0f}% (기준 85% 이하)",
    ]
    return dict(loop_a=loop_a, loop_b=loop_b, r_max=r_max, culprit=culprit, causes=causes, actions=actions, expansion_stage=expansion_stage, evidence=evidence)

def zone(title: str, tag: str, tag_color: str, strong: bool = False):
    cls = "zone zone-strong" if strong else "zone"
    tag_html = f'<span class="badge" style="border-color:{tag_color}; color:{tag_color}; background: rgba(255,255,255,0.04)">{tag}</span>'
    st.markdown(f'<div class="{cls}"><div class="zone-titlebar"><div class="zone-title">{title}</div>{tag_html}</div>', unsafe_allow_html=True)

def end_zone():
    st.markdown("</div>", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### Bio-OS 콘솔")
st.sidebar.markdown('<div class="small-muted">투자자용 프리미엄 콘솔</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")
# 데모 시나리오 선택(투자자/정부 설명용)
scenario = st.sidebar.radio(
    "데모 시나리오",
    ["일반", "산소량 급락", "물 흐름 저하", "여과 부담 증가"],
    index=0
)

st.sidebar.info("※ 현재 화면은 데모(샘플 데이터) 기반입니다.\n실증 단계에서는 실제 센서/DB 값으로 자동 전환됩니다.")


st.sidebar.markdown("### 제출 정보")
facility_name = st.sidebar.text_input("시설명", value="BioModule 150")
report_period = st.sidebar.text_input("보고 기간", value="(예: 2026-02-10 ~ 2026-02-16)")
report_owner = st.sidebar.text_input("작성/담당", value="(예: 운영팀)")
system_version = st.sidebar.text_input("시스템 버전", value="Bio-OS v1.0")

doc_id = st.sidebar.text_input("문서 번호", value="BIO-OS-DOC-001")
rev = st.sidebar.text_input("개정(Rev.)", value="v1.0")
issuer = st.sidebar.text_input("발행 기관/회사", value="(예: BioModule Lab)")
logo_text = st.sidebar.text_input("로고(텍스트)", value="Bio-OS")

st.sidebar.markdown("### 개정 이력")
rev_date = st.sidebar.text_input("개정 일자", value="2026-02-18")
rev_desc = st.sidebar.text_input("개정 내용", value="최초 발행")
st.sidebar.markdown("### 보고서")
c1, c2 = st.sidebar.columns(2)
with c1:
    make_summary = st.button("1페이지 요약")
with c2:
    make_detail = st.button("3페이지 상세")

if make_summary or make_detail:
    payload = build_report_payload(m, facility_name, report_period, report_owner, system_version, doc_id, rev, issuer, logo_text, rev_date, rev_desc)
    pdf_bytes = make_pdf(summary_only=make_summary, payload=payload)
    fname = "Bio-OS_운영_요약보고서_1p.pdf" if make_summary else "Bio-OS_운영_상세보고서_3p.pdf"
    st.sidebar.download_button(
        label="PDF 다운로드",
        data=pdf_bytes,
        file_name=fname,
        mime="application/pdf",
        use_container_width=True
    )
st.sidebar.selectbox("데모 시나리오", ["Normal", "Oxygen Drop", "Pump Degradation", "Filter Stress"], index=0)
show_english = False  # 한글 표준 고정
st.sidebar.caption("※ 내부 로직/파라미터는 유지하고, 화면 표시는 표준 한글로 제공합니다.")

m = load_latest_metrics(scenario)
r_max = m["r_max"]

# ZONE 1
zone("구역 1 · 전체 위험", "위험 요약", "#2A57FF", strong=True)
col1, col2, col3 = st.columns([1.2, 1.1, 1.3], gap="large")
with col1:
    st.markdown(f'<div class="{risk_badge_class(r_max)}">현재 상태: {risk_label(r_max)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-big">{r_max:.0f} <span class="small-muted">/ 100</span></div>', unsafe_allow_html=True)
    sub = f"전체 위험은 {m['culprit']} 기준입니다."
    st.markdown(f'<div class="kpi-sub">{sub}</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card"><div class="card-title">주요 원인(상위 3개)</div>', unsafe_allow_html=True)
    for i, (c, why) in enumerate(m["causes"], start=1):
        extra = ''
        st.markdown(f"{i}. **{c}** <span class='small-muted'>{extra}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card"><div class="card-title">조치 안내(우선순위)</div>', unsafe_allow_html=True)
    for p, txt, when in m["actions"]:
        pill_cls = "pill p1" if p == "P1" else ("pill p2" if p == "P2" else "pill p3")
        p_label = {"P1":"지금 바로 조치","P2":"오늘 안에 점검","P3":"계획 수립 필요"}.get(p, p)
        st.markdown(f"<span class='{pill_cls}'>{p_label}</span>  {txt}", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
kpis = [
    ("전체 위험 점수", f"{r_max:.0f}/100", "전체 위험 점수(최대값 기준)"),
    ("갑작스런 변화(24시간)", f"{m['loop_a']['shock_24h'] + m['loop_b']['shock_24h']}", "갑작스런 변화 합계(임시)"),
    ("위험 노출 시간(7일)", f"{max(m['loop_a']['exposure_7d'], m['loop_b']['exposure_7d'])*100:.0f}%", "최근 7일 위험 노출(임시 환산)"),
    ("설비 사용률", f"{max(m['loop_a']['util'], m['loop_b']['util'])*100:.0f}%", "설비 사용률(임시)"),
]
for title, value, note in kpis:
    st.markdown(f"""
      <div class="card">
        <div class="card-title">{title}</div>
        <div class="kpi-big">{value}</div>
        <div class="note">{note}</div>
      </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
end_zone()

# ZONE 2 + 3
left, right = st.columns([1.1, 0.9], gap="large")
with left:
    zone("구역 2 · 구역 비교", "A구역 / B구역", "#1BE7FF")
    df = pd.DataFrame([
        {"구역": "Loop A", "상태": risk_label(m["loop_a"]["risk"]), "전체 위험 점수": m["loop_a"]["risk"], "급변(24h)": m["loop_a"]["shock_24h"],
         "위험노출(7d)": f"{m['loop_a']['exposure_7d']*100:.0f}%", "설비부담률": f"{m['loop_a']['util']*100:.0f}%"},
        {"구역": "Loop B", "상태": risk_label(m["loop_b"]["risk"]), "전체 위험 점수": m["loop_b"]["risk"], "급변(24h)": m["loop_b"]["shock_24h"],
         "위험노출(7d)": f"{m['loop_b']['exposure_7d']*100:.0f}%", "설비부담률": f"{m['loop_b']['util']*100:.0f}%"},
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 글로벌(관리자) 보고서")
admin_mode = st.sidebar.toggle("글로벌 보고서 표시", value=False, help="현장 화면은 한글 고정. 글로벌 제출/홍보용 영문 PDF만 별도 제공.")
if admin_mode:
    g1, g2 = st.sidebar.columns(2)
    with g1:
        make_summary_en = st.button("영문 1p")
    with g2:
        make_detail_en = st.button("영문 3p")
    if make_summary_en or make_detail_en:
        payload = build_report_payload(m, facility_name, report_period, report_owner, system_version, doc_id, rev, issuer, logo_text, rev_date, rev_desc)
        pdf_bytes = make_pdf_en(summary_only=make_summary_en, payload=payload)
        fname = "Bio-OS_Report_EN_1p.pdf" if make_summary_en else "Bio-OS_Report_EN_3p.pdf"
        st.sidebar.download_button(
            label="영문 PDF 다운로드",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
            use_container_width=True
        )
    st.markdown('<div class="card"><div class="card-title">근거(현재값/기준)</div>', unsafe_allow_html=True)
    for e in m["evidence"]:
        st.markdown(f"- {e}")
    st.markdown("</div>", unsafe_allow_html=True)
    end_zone()

with right:
    zone("구역 3 · 자본 효율", "설비·확장", "#B28DFF")
    st.markdown(f"<div class='card'><div class='card-title'>증설 판단 단계</div><div class='kpi-big'>{m['expansion_stage']}</div><div class='note'>과잉투자 없이, 데이터로 증설 타이밍을 결정</div></div>", unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown("<div class='card'><div class='card-title'>설비 사용률(임시)</div>", unsafe_allow_html=True)
    st.progress(int(m["loop_a"]["util"]*100), text=f"Loop A 부담률 {m['loop_a']['util']*100:.0f}%")
    st.progress(int(m["loop_b"]["util"]*100), text=f"Loop B 부담률 {m['loop_b']['util']*100:.0f}%")
    st.markdown("</div>", unsafe_allow_html=True)
    end_zone()

# ZONE 4
zone("구역 4 · 추세", "추세·급변", "#93A4B7")
now = datetime.now()
t = pd.date_range(now - timedelta(hours=24), now, freq="15min")
risk_series = np.clip(np.linspace(40, r_max, len(t)) + np.random.normal(0, 2.0, len(t)), 0, 100)
do_series = np.clip(np.linspace(7.8, m["loop_a"]["do"], len(t)) + np.random.normal(0, 0.08, len(t)), 0, 12)
util_series = np.clip(np.linspace(0.55, m["loop_a"]["util"], len(t)) + np.random.normal(0, 0.015, len(t)), 0, 1)
ts = pd.DataFrame({"time": t, "risk": risk_series, "do": do_series, "util": util_series}).set_index("time")
st.line_chart(ts[["risk"]], height=190)
st.line_chart(ts[["do"]], height=190)
st.line_chart(ts[["util"]], height=190)
st.caption("※ 그래프는 샘플 데이터입니다. Seed-M1 DB/API 연결 시 실제 운영 추세로 교체됩니다.")
end_zone()

st.markdown('<div class="small-muted">Bio-OS v1.0 · 프리미엄 콘솔 (Streamlit) · 표시 전용</div>', unsafe_allow_html=True)

# =====================================================
# Ultimate Package: Security + KPI Chart + Strategy + Whitepaper
# =====================================================
import matplotlib.pyplot as plt
from reportlab.platypus import Image

st.sidebar.markdown("### 문서 보안 등급")
security_level = st.sidebar.selectbox("보안 등급", ["일반 공개", "내부 전용", "대외비"])

def generate_kpi_chart(payload):
    fig = plt.figure()
    values = [payload["r_max"]*0.6, payload["r_max"]*0.7, payload["r_max"]*0.8,
              payload["r_max"]*0.9, payload["r_max"]*0.85, payload["r_max"]*0.75,
              payload["r_max"]]
    plt.plot(values)
    plt.title("7-Day Risk Trend")
    plt.xlabel("Day")
    plt.ylabel("Risk Score")
    chart_path = "/mnt/data/temp_chart.png"
    plt.savefig(chart_path)
    plt.close(fig)
    return chart_path

def make_whitepaper(payload):
    from io import BytesIO
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    elements = []
    elements.append(Paragraph("Bio-OS Global Standard Whitepaper", styles["Heading1"]))
    elements.append(Spacer(1, 12))
    sections = [
        "1. Executive Vision",
        "2. Problem Definition (Aquaculture Risk)",
        "3. Unified Risk Score Architecture",
        "4. Operational Decision Loop",
        "5. Cost Minimization Strategy",
        "6. Scale-out Model (Seed-M1 → BioModule150)",
        "7. Government Impact",
        "8. Global Standardization Strategy",
        "9. Terminology Framework",
        "10. KPI Evidence Model",
        "11. Deployment Model",
        "12. Future Expansion (Multi-Species / Multi-Industry)"
    ]
    for s in sections:
        elements.append(Paragraph(s, styles["Heading2"]))
        elements.append(Paragraph("Standardized architecture and scalable governance model.", body))
        elements.append(PageBreak())
    doc.build(elements)
    return buf.getvalue()

st.sidebar.markdown("### Ultimate 문서 패키지")
if st.sidebar.button("Ultimate 패키지 생성"):
    payload = build_report_payload(
        m, facility_name, report_period, report_owner, system_version,
        doc_id, rev, issuer, logo_text, rev_date, rev_desc
    )
    chart_path = generate_kpi_chart(payload)
    whitepaper_pdf = make_whitepaper(payload)
    st.sidebar.success("Whitepaper 생성 완료")
    st.sidebar.download_button(
        "글로벌 백서 다운로드 (12p)",
        whitepaper_pdf,
        file_name="Bio-OS_Global_Whitepaper.pdf",
        mime="application/pdf"
    )
