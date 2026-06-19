# 개인정보 동의서 점검 도구 (consent_reviewer)

개인정보 보호법령을 기준으로 **개인정보 수집·이용 동의서**를 점검하고, 결과를 **엑셀**로 출력하는 도구입니다.

판단은 **별도 API 호출(과금) 없이 Claude Code가 동의서를 직접 읽고 수행**합니다.
단순 문자열/패턴 매칭이 아니라 **내용의 법적 타당성**을 판단합니다.
예) "보유기간: 거래 종료 후 2년" → 그 기간이 수집 목적·법정 보존의무에 비추어 적정한지 판단합니다.

> Python은 결정적 작업(문서 파싱·엑셀 생성)만 담당하고, 법적 판단은 Claude Code가 합니다.
> 따라서 ANTHROPIC_API_KEY 가 필요 없고 API 사용료도 발생하지 않습니다.

## 점검 근거
- 개인정보 보호법 및 시행령
- 표준 개인정보 보호지침(표준지침)
- 개인정보의 안전성 확보조치 기준(고시)
- 개인정보보호위원회 표준 동의서 양식·안내서

## 점검 항목(11개)
수집·이용 목적(제15조) / 수집 항목·최소수집(제16조) / **보유·이용 기간 및 기간 적정성(제15·21조 + 개별법 법정 보존기간)** / 동의 거부권 및 불이익 고지(제22조) / 제3자 제공(제17조) / 민감정보 별도동의(제23조) / 고유식별정보 별도동의(제24조) / 주민등록번호 처리 제한(제24조의2) / 처리 위탁(제26조) / 만 14세 미만 아동 법정대리인 동의(제22조의2) / 동의 방법·명확성(표준지침·표준 동의서 양식)

## 지원 입력 형식
TXT · Word(.docx) · HTML · PDF · 이미지(.png/.jpg/.jpeg/.webp/.gif)
> PDF/이미지(스캔본 포함)는 Claude Code가 파일을 직접 열람해 판단합니다(별도 OCR 불필요).

## 설치
```bash
pip install -r requirements.txt
```
Python 3.10 이상 권장. (WSL/Windows 모두 동작)

## 사용법 (3단계)
판단을 Claude Code가 수행하므로, 보통은 Claude Code 세션에서 "이 동의서 점검해줘"라고 요청하면
아래 절차를 자동으로 진행합니다. 수동 절차는 다음과 같습니다.

```bash
# 1) 추출: 동의서를 파싱해 리뷰 패킷(본문+점검표+법령컨텍스트) 생성
python -m consent_reviewer extract 동의서.pdf docs/*.docx --out review_packet.json

# 2) 판단: Claude Code가 패킷/문서를 읽고 findings.json 작성
#    (틀이 필요하면) python -m consent_reviewer skeleton 동의서.pdf --out findings.json

# 3) 리포트: 판단 결과로 엑셀 생성
python -m consent_reviewer report findings.json --out 동의서_점검결과.xlsx
```
자세한 판단 절차는 [REVIEW_GUIDE.md](REVIEW_GUIDE.md) 참고.

## 출력
엑셀: **요약 시트** + **문서별 상세 시트**
- 상세: 번호 · 점검 영역 · 세부 점검항목 · 판정 · 근거(인용) · 미흡 사유 · 개선 권고 · 신뢰도 · 근거 법령 (판정/신뢰도 색상)
- 판정: `적합` / `보완필요` / `누락` / `해당없음`

## 구조
```
consent_reviewer/
├── consent_reviewer/
│   ├── models.py      # 공유 데이터 계약(Pydantic)
│   ├── config.py      # 리포트 상수
│   ├── parser.py      # 멀티포맷 입력 → ParsedDocument
│   ├── knowledge.py   # 점검 항목 + 법령 지식 컨텍스트
│   ├── report.py      # 엑셀 리포트
│   └── cli.py         # extract / skeleton / report 진입점
├── knowledge_base/legal_requirements.md  # 법령 근거 정리
├── REVIEW_GUIDE.md    # Claude Code 판단 절차
└── samples/           # 테스트 샘플
```

## 한계 및 주의
- 자동 판정은 **1차 스크리닝**입니다. 최종 적합성은 전문가(개인정보 보호책임자/법무) 검토가 필요합니다.
- 점검 대상은 **빈 양식/템플릿** 기준입니다. 실제 정보주체의 개인정보가 채워진 문서를 점검할 경우 취급에 유의하세요.
- 법령은 개정될 수 있으므로, 중요한 판단은 `knowledge_base/legal_requirements.md`의 근거와 현행 법령을 함께 확인하세요.
