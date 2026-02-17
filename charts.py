from __future__ import annotations
from typing import List
import io
import matplotlib.pyplot as plt

def make_7d_trend_png(risk_max: float) -> bytes:
    """
    데모용 7일 추세 그래프(PNG bytes).
    - Streamlit Cloud 환경에서도 안전하게 BytesIO로만 처리
    """
    # 간단한 형태의 추세(근거용): 현재 위험을 기준으로 완만한 변동을 생성
    base = float(risk_max)
    vals = [
        max(0.0, min(100.0, base*0.60)),
        max(0.0, min(100.0, base*0.70)),
        max(0.0, min(100.0, base*0.80)),
        max(0.0, min(100.0, base*0.90)),
        max(0.0, min(100.0, base*0.85)),
        max(0.0, min(100.0, base*0.75)),
        max(0.0, min(100.0, base)),
    ]

    fig = plt.figure()
    plt.plot(vals)
    plt.title("7일 전체 위험 점수 추세(데모)")
    plt.xlabel("일")
    plt.ylabel("점수")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
