# Bio-OS 프리미엄 Console (Streamlit)

프리미엄 투자자용 콘솔 레이아웃(Zone 분리/테두리/타이틀바/카드)을 Streamlit에서 구현한 뼈대입니다.

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 연결 포인트
- `load_latest_metrics()`를 Seed-M1 DB/API 호출로 교체하면, KPI/Loop 비교/근거/증설 단계가 실제 값으로 출력됩니다.
- 내부 로직/파라미터는 변경하지 않고, 외부 표현(전문가 톤)만 담당합니다.


## 한글 표준 고정
- 화면에 영어 표기는 나오지 않도록 기본값을 한글로 고정했습니다.


## 용어 표준(현장용)
- 안정→정상, 경고→경계
- 리스크 지수→전체 위험 점수
- 급변 이벤트→갑작스런 변화
- 노출→위험 노출 시간
- 부담률/Utilization→설비 사용률
- P1/P2/P3는 화면에서 한글(지금 바로 조치/오늘 안에 점검/계획 수립 필요)로 표기
