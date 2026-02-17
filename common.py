from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Tuple

def risk_label_kr(score: float) -> str:
    if score < 40: return "정상"
    if score < 60: return "주의"
    if score < 75: return "경계"
    return "위험"

def risk_label_en(score: float) -> str:
    if score < 40: return "Normal"
    if score < 60: return "Caution"
    if score < 75: return "Watch"
    return "Critical"

@dataclass
class DocMeta:
    facility_name: str = "BioModule 150"
    report_period: str = "(예: 2026-02-10 ~ 2026-02-16)"
    report_owner: str = "(예: 운영팀)"
    system_version: str = "Bio-OS v1.0"
    doc_id: str = "BIO-OS-DOC-001"
    rev: str = "v1.0"
    issuer: str = "(예: BioModule Lab)"
    logo_text: str = "Bio-OS"
    security_level: str = "일반 공개"   # 일반 공개 / 내부 전용 / 대외비
    rev_date: str = datetime.now().strftime("%Y-%m-%d")
    rev_desc: str = "최초 발행"

def build_report_payload(m: Dict[str, Any], meta: DocMeta) -> Dict[str, Any]:
    la, lb = m["loop_a"], m["loop_b"]
    r_max = float(max(la["risk"], lb["risk"]))
    culprit = "A구역" if la["risk"] >= lb["risk"] else "B구역"
    status = risk_label_kr(r_max)

    causes_pairs = m.get("causes", [])
    if not causes_pairs:
        causes_pairs = [("특이 이상 없음", 1.0)]
    causes_top = causes_pairs[:3]
    actions = m.get("actions", [])
    p1 = actions[0][1] if actions else "운영 조건 점검"

    shock = int(la["shock_24h"] + lb["shock_24h"])
    exposure = float(max(la["exposure_7d"], lb["exposure_7d"])) * 100.0
    util = float(max(la["util"], lb["util"])) * 100.0

    if r_max >= 75:
        stage = "즉시 증설 검토"
    elif r_max >= 60:
        stage = "설비 증설 준비"
    elif r_max >= 40:
        stage = "운영 조정 필요"
    else:
        stage = "설비 여유 있음"

    payload = {
        "meta": meta.__dict__.copy(),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "r_max": r_max,
        "culprit": culprit,
        "causes": causes_top,
        "causes_top_names": [c for c, _ in causes_top],
        "p1": p1,
        "shock_24h": shock,
        "exposure_7d_pct": exposure,
        "util_pct": util,
        "expansion_stage": stage,
        "evidence": m.get("evidence", []),
        "loop_a": la,
        "loop_b": lb,
    }
    return payload
