# 점검 수행 가이드 (Claude Code용)

이 도구는 **별도 API 호출(과금) 없이**, **Claude Code가 동의서를 직접 읽고 판단**한다.
Python은 결정적인 작업(파싱·엑셀 생성)만 담당하고, 법적 타당성 판단은 Claude Code가 한다.

## 표준 절차

### 1) 추출 — 리뷰 패킷 생성
```bash
python -m consent_reviewer extract <동의서 파일들> --out review_packet.json
```
`review_packet.json`에는 다음이 담긴다.
- `legal_context`: 판단 기준이 되는 법령 컨텍스트(점검항목별 근거·기준, 보유기간 적정성 규칙, 판단 예시)
- `checklist`: 11개 점검 항목(item_id/area/item_name/law_basis/judgment_criteria/conditional)
- `documents`: 문서별 `{source_path, file_type, text, needs_visual_read, empty, note}`
  - `text`가 있으면 그 본문으로 판단.
  - `needs_visual_read=true`(이미지/스캔 PDF)이면 **해당 파일을 Read 도구로 직접 열람**해 판단.

### 2) 판단 — Claude Code가 직접 수행 (핵심)
`review_packet.json`의 `legal_context`와 `checklist`를 기준으로, 각 문서의 본문(또는 직접 열람한 이미지)을
읽고 **11개 항목 각각**에 대해 판정한다. **단순히 문구가 있는지가 아니라 그 내용이 법적으로 타당한지** 판단한다.
예) 보유기간이 적혀 있어도 그 기간이 수집 목적·법정 보존의무에 부합하는지까지 본다.

각 항목 판정:
- `verdict`: `적합` / `보완필요` / `누락` / `해당없음`
  - 적합: 요건 충족 / 보완필요: 있으나 부정확·과도·불명확·위반소지 / 누락: 빠짐 / 해당없음: 조건부 항목인데 해당 처리 없음
- `found_content`: 문서에서 인용한 실제 근거 문구(없으면 빈 문자열)
- `issue`: 미흡 사유(적합이면 빈 문자열)
- `recommendation`: 개선 권고(적합이면 빈 문자열)
- `confidence`: 판단 신뢰도(`높음`/`중간`/`낮음`)
- `legal_basis`: 비우면 점검표의 근거 법령이 자동 사용됨(특정 조문을 강조하려면 채운다)

결과를 `findings.json`으로 저장한다. (틀이 필요하면 `python -m consent_reviewer skeleton <파일들> --out findings.json` 로 생성 후 채운다.)

`findings.json` 형식:
```json
{
  "results": [
    {
      "source_path": "samples/sample_bad.txt",
      "overall_summary": "다수 항목 보완 필요 ...",
      "findings": [
        {"item_id": "retention", "verdict": "보완필요",
         "found_content": "보유 기간: 영구 보관",
         "issue": "제21조상 목적 달성 후 파기 원칙 위반, 법정 근거 없음",
         "recommendation": "목적 달성 시 파기하고 법정 보존정보는 근거·기간 명시",
         "confidence": "높음"}
      ]
    }
  ]
}
```

### 3) 리포트 — 엑셀 생성
```bash
python -m consent_reviewer report findings.json --out 동의서_점검결과.xlsx
```
요약 시트 + 문서별 상세 시트(번호·점검영역·세부항목·판정·근거(인용)·미흡사유·개선권고·신뢰도·근거법령)가 생성된다.

## 주의
- 자동 판정은 1차 스크리닝이며 최종 적합성은 전문가 검토가 필요하다.
- 점검 대상은 빈 양식/템플릿 기준. 실제 개인정보가 채워진 문서를 다룰 때는 취급에 유의한다.
