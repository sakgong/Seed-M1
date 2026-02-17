# Bio-OS Streamlit Console (Modular)

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 배포(Streamlit Cloud)
- Repository root에 아래 파일이 있어야 합니다.
  - app.py
  - requirements.txt
  - common.py
  - charts.py
  - report_kr.py
  - report_en.py
  - whitepaper.py

## 기능
- 현장 표준 한글 UI 고정
- 데모 시나리오 3종
- PDF: 1페이지 요약 / 3페이지 상세(정부 제출용 섹션 포함)
- 문서번호/Rev./발행기관/보안등급/개정이력 헤더/푸터 자동 적용
- 글로벌(관리자): 영문 PDF(Glossary 포함) + 12p Whitepaper
