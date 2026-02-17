from __future__ import annotations
import streamlit as st
from datetime import datetime

from common import DocMeta, build_report_payload
from report_kr import make_pdf_kr
from report_en import make_pdf_en
from whitepaper import make_whitepaper_12p

# -----------------------------
# UI 기본 설정
# -----------------------------
st.set_page_config(page_title="Bio-OS 콘솔", layout="wide")

CSS = """
<style>
body {font-family: sans-serif;}
.zone {border:1px solid rgba(0,0,0,0.10); border-radius:14px; padding:14px; margin-bottom:12px;}
.zone h3 {margin:0 0 8px 0;}
.kpi {display:flex; gap:10px; flex-wrap:wrap;}
.kpi .card {border:1px solid rgba(0,0,0,0.10); border-radius:14px; padding:12px 14px; min-width:220px;}
.pill {display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; margin-right:6px;}
.p1{background:rgba(255,0,0,0.10);}
.p2{background:rgba(255,165,0,0.12);}
.p3{background:rgba(0,128,255,0.10);}
.small {font-size:12px; opacity:0.85;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------
# 데모 데이터 (Seed-M1 실제 DB 연동 전)
# -----------------------------
def load_latest_metrics(scenario: str = "일반") -> dict:
    # 기본값(일반)
    loop_a = dict(risk=52, shock_24h=1, exposure_7d=0.18, util=0.74, do=7.1, temp=16.7, ph=7.82, sal=31.1)
    loop_b = dict(risk=44, shock_24h=0, exposure_7d=0.12, util=0.61, do=7.4, temp=16.6, ph=7.88, sal=31.0)

    if scenario == "산소량 급락":
        loop_a.update(dict(risk=82, shock_24h=9, exposure_7d=0.48, util=0.92, do=5.3, temp=16.8, ph=7.68, sal=31.2))
        loop_b.update(dict(risk=34, shock_24h=0, exposure_7d=0.05, util=0.38, do=7.7, temp=16.6, ph=7.92, sal=31.0))
        causes = [("산소량 급락", 0.52), ("출렁임 증가", 0.31), ("설비 사용률 상승", 0.17)]
        actions = [("P1","산소 공급 단계 상향","즉시"), ("P2","산소 라인 점검","오늘"), ("P3","여유 용량 검토","계획")]
    elif scenario == "물 흐름 저하":
        loop_a.update(dict(risk=63, shock_24h=2, exposure_7d=0.28, util=0.88, do=6.6, temp=16.7, ph=7.74, sal=31.1))
        loop_b.update(dict(risk=41, shock_24h=1, exposure_7d=0.12, util=0.62, do=7.2, temp=16.6, ph=7.88, sal=31.0))
        causes = [("물 흐름 저하", 0.46), ("설비 사용률 상승", 0.29), ("산소량 변동", 0.25)]
        actions = [("P1","펌프/밸브 점검 및 유량 복구","즉시"), ("P2","배관/필터 점검","오늘"), ("P3","예비 펌프/라인 계획","계획")]
    elif scenario == "여과 부담 증가":
        loop_a.update(dict(risk=58, shock_24h=1, exposure_7d=0.22, util=0.84, do=6.9, temp=16.8, ph=7.55, sal=31.2))
        loop_b.update(dict(risk=46, shock_24h=0, exposure_7d=0.15, util=0.66, do=7.4, temp=16.6, ph=7.83, sal=31.0))
        causes = [("여과 부담 증가", 0.44), ("pH 하락", 0.33), ("설비 사용률 상승", 0.23)]
        actions = [("P1","여과 단계 강화/역세척 점검","즉시"), ("P2","pH 안정화 점검","오늘"), ("P3","여과 용량 증설 검토","계획")]
    else:
        causes = [("정상 변동", 0.41), ("운영 조건", 0.33), ("설비 사용률", 0.26)]
        actions = [("P2","일일 점검 수행","오늘"), ("P3","운영 기록 정리","계획")]

    evidence = [
        f"산소량(용존산소) {loop_a['do']:.1f} (기준 6.0~10.0)",
        f"물 온도 {loop_a['temp']:.1f} (기준 14.0~20.0)",
        f"물 산도(pH) {loop_a['ph']:.2f} (기준 7.6~8.3)",
        f"염도 {loop_a['sal']:.1f} (기준 28.0~34.0)",
    ]

    return dict(loop_a=loop_a, loop_b=loop_b, causes=causes, actions=actions, evidence=evidence)

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.markdown("## Bio-OS 콘솔")
st.sidebar.caption("표준 한글 고정(현장용)")

st.sidebar.markdown("---")
scenario = st.sidebar.radio("데모 시나리오", ["일반", "산소량 급락", "물 흐름 저하", "여과 부담 증가"], index=0)
st.sidebar.info("※ 현재 화면은 데모(샘플 데이터) 기반입니다.\n실증 단계에서는 실제 센서/DB 값으로 자동 전환됩니다.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 제출 정보")
meta = DocMeta(
    facility_name=st.sidebar.text_input("시설명", value="BioModule 150"),
    report_period=st.sidebar.text_input("보고 기간", value="(예: 2026-02-10 ~ 2026-02-16)"),
    report_owner=st.sidebar.text_input("작성/담당", value="(예: 운영팀)"),
    system_version=st.sidebar.text_input("시스템 버전", value="Bio-OS v1.0"),
    doc_id=st.sidebar.text_input("문서 번호", value="BIO-OS-DOC-001"),
    rev=st.sidebar.text_input("개정(Rev.)", value="v1.0"),
    issuer=st.sidebar.text_input("발행 기관/회사", value="(예: BioModule Lab)"),
    logo_text=st.sidebar.text_input("로고(텍스트)", value="Bio-OS"),
    security_level=st.sidebar.selectbox("보안 등급", ["일반 공개", "내부 전용", "대외비"]),
    rev_date=st.sidebar.text_input("개정 일자", value=datetime.now().strftime("%Y-%m-%d")),
    rev_desc=st.sidebar.text_input("개정 내용", value="최초 발행"),
)

# -----------------------------
# 메트릭 로드
# -----------------------------
m = load_latest_metrics(scenario)
payload = build_report_payload(m, meta)

# -----------------------------
# 메인 화면
# -----------------------------
st.title("Bio-OS 프리미엄 콘솔")
st.caption("현장 표준 한글(영어 0%) · 상태 → 원인 → 조치 · 보고서 자동 생성")

# KPI
r_max = payload["r_max"]
status = payload["status"]
culprit = payload["culprit"]
st.markdown(f"### 현재 상태: **{status}**  ·  전체 위험 점수(최대값): **{r_max:.0f}/100**  ·  기준: **{culprit}**")

st.markdown('<div class="kpi">', unsafe_allow_html=True)
def card(title, value, note=""):
    st.markdown(f"""
    <div class="card">
      <div class="small">{title}</div>
      <div style="font-size:26px; font-weight:700;">{value}</div>
      <div class="small">{note}</div>
    </div>
    """, unsafe_allow_html=True)

card("전체 위험 점수", f"{r_max:.0f}", "0~100")
card("갑작스런 변화(24시간)", f"{payload['shock_24h']}", "횟수")
card("위험 노출 시간(7일)", f"{payload['exposure_7d_pct']:.0f}%", "임시 환산")
card("설비 사용률", f"{payload['util_pct']:.0f}%", "임시")
st.markdown("</div>", unsafe_allow_html=True)

col1, col2 = st.columns([1.2, 0.8])

with col1:
    st.markdown('<div class="zone">', unsafe_allow_html=True)
    st.subheader("주요 원인(상위 3개)")
    for c, w in payload["causes"]:
        st.write(f"• {c} ({w:.0%})")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="zone">', unsafe_allow_html=True)
    st.subheader("근거(현재값/기준)")
    for e in payload["evidence"][:6]:
        st.write(f"• {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="zone">', unsafe_allow_html=True)
    st.subheader("조치 안내(우선순위)")
    for p, txt, when in m["actions"]:
        p_label = {"P1":"지금 바로 조치","P2":"오늘 안에 점검","P3":"계획 수립 필요"}.get(p, p)
        cls = "p1" if p == "P1" else ("p2" if p == "P2" else "p3")
        st.markdown(f"<span class='pill {cls}'>{p_label}</span> {txt}", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="zone">', unsafe_allow_html=True)
    st.subheader("증설 판단 단계")
    st.write(f"• {payload['expansion_stage']}")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# 보고서 생성/다운로드
# -----------------------------
st.markdown("## 보고서")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("1페이지 요약 PDF"):
        pdf = make_pdf_kr(summary_only=True, payload=payload)
        st.download_button("다운로드(요약)", pdf, file_name="Bio-OS_운영_요약보고서_1p.pdf", mime="application/pdf")
with c2:
    if st.button("3페이지 상세 PDF(정부용 포함)"):
        pdf = make_pdf_kr(summary_only=False, payload=payload)
        st.download_button("다운로드(상세)", pdf, file_name="Bio-OS_운영_상세보고서_3p.pdf", mime="application/pdf")
with c3:
    admin = st.toggle("글로벌(관리자) 모드", value=False, help="현장 UI는 한글 고정. 영문/백서는 관리자용 출력물입니다.")

if admin:
    st.markdown("### 글로벌(관리자) 출력")
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("영문 1p PDF"):
            pdf = make_pdf_en(summary_only=True, payload=payload)
            st.download_button("다운로드(EN 1p)", pdf, file_name="Bio-OS_Report_EN_1p.pdf", mime="application/pdf")
    with a2:
        if st.button("영문 3p PDF(Glossary 포함)"):
            pdf = make_pdf_en(summary_only=False, payload=payload)
            st.download_button("다운로드(EN 3p)", pdf, file_name="Bio-OS_Report_EN_3p.pdf", mime="application/pdf")
    with a3:
        if st.button("글로벌 백서 12p"):
            pdf = make_whitepaper_12p(payload)
            st.download_button("다운로드(Whitepaper)", pdf, file_name="Bio-OS_Global_Whitepaper_12p.pdf", mime="application/pdf")

st.caption("※ 데모(샘플 데이터) 기반. 실증 단계에서는 Seed-M1 센서/DB 연동으로 자동 전환.")
