# 개인정보 컴플라이언스 점검 도구 모음

개인정보 보호법 기준으로 **동의서**와 **처리방침**을 자동 점검하는 도구 모음입니다.
ISMS-P / 개인정보보호 컨설팅 실무용 1차 스크리닝 도구입니다.

## 구성

```
privacy_compliance_tools/
├── consent_checker/        # 개인정보 동의서 점검 (제15·16·17·21·22·24·37조)
│   ├── run.py              #   실행 진입점
│   ├── clause_checker.py   #   필수 조항 점검 엔진
│   ├── format_checker.py   #   서식(폰트·Bold) 점검
│   ├── rules.py            #   점검 룰 정의
│   └── doc_parser.py       #   PDF 파서
├── policy_checker/         # 개인정보처리방침 점검 (제30조)
│   ├── policy_checker.py   #   실행 진입점 + 엔진 + 파서
│   └── policy_rules.py     #   점검 룰 정의 (일반/금융)
├── samples/                # 테스트용 샘플 (선택)
├── requirements.txt
└── README.md
```

## 설치
```bash
pip install -r requirements.txt
```

## 사용법

### 1) 동의서 점검
```bash
cd consent_checker
python run.py 동의서.pdf
python run.py 동의서.pdf --out 결과.txt
```
판정: `[발견] / [내용미비] / [누락] / [해당없음]`

점검 항목(7): 수집·이용 목적, 수집 항목, 보유·이용 기간, 동의 거부 권리,
제3자 제공, 고유식별정보 처리 동의, 동의 철회

### 2) 처리방침 점검
```bash
cd policy_checker
python policy_checker.py 처리방침.pdf --mode general   # 일반기업
python policy_checker.py 처리방침.pdf --mode finance   # 금융기관
python policy_checker.py 처리방침.pdf --mode finance --out 결과.txt
```
판정: `[적합] / [보완필요] / [누락] / [해당없음]`

점검 항목: 처리목적·보유기간·항목·제3자제공·위탁·정보주체권리·보호책임자·
쿠키·안전성조치·권익침해구제·변경시행일 (+조건부: 국외이전·가명정보·CCTV·
자동화결정, +금융전용: 신용정보법)

## 검증 이력 (현재까지)
- 동의서: 채용/금융(미쓰이)/보금자리론/보험(한화) 5종 양식 교차 검증 완료
- 처리방침: 일반·부실·금융 3종 시나리오 검증 완료

## 룰 수정 방법
- 동의서: `consent_checker/rules.py`의 `MANDATORY_CLAUSES`
- 처리방침: `policy_checker/policy_rules.py`의 `MANDATORY_ITEMS`

각 룰은 헤더 패턴 / 내용 검증 패턴 / 필수 필드 / 근거 법령으로 구성됩니다.
새 양식에서 오탐이 나오면 해당 룰의 패턴을 보강하고, 기존 양식으로 회귀 테스트하세요.

## 한계
- 텍스트 레이어 있는 PDF에서 가장 정확. 스캔/이미지 PDF는 OCR 선행 필요.
- 서식 점검(폰트·Bold)은 PDF에 서식 메타데이터가 있을 때만 유효.
- HWP 원본을 변환 없이 직접 점검하려면 HWP 파서 추가 필요(향후 과제).
- 자동 판정은 1차 스크리닝이며, 최종 적합 판단은 전문가 검토 필요.
