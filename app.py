import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
def load_latest_metrics():
    loop_a = dict(risk=68, shock_24h=4, exposure_7d=0.32, util=0.86, do=6.2, temp=16.8, ph=7.72, sal=31.2)
    loop_b = dict(risk=31, shock_24h=0, exposure_7d=0.06, util=0.40, do=7.6, temp=16.6, ph=7.92, sal=31.0)
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
st.sidebar.selectbox("데모 시나리오", ["Normal", "Oxygen Drop", "Pump Degradation", "Filter Stress"], index=0)
show_english = False  # 한글 표준 고정
st.sidebar.caption("※ 내부 로직/파라미터는 유지하고, 화면 표시는 표준 한글로 제공합니다.")

m = load_latest_metrics()
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
