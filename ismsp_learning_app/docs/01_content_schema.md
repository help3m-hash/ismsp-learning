# 콘텐츠 스키마 (인증기준 1건 = JSON 1파일)

`content/items/<id>.json` — 항목 1개. 외부 QA는 모든 텍스트를 원문(`content/raw/`)과 대조한다.

```jsonc
{
  "id": "1.1.1",
  "domain": "1. 관리체계 수립 및 운영",
  "category": "1.1 관리체계 기반 마련",
  "title": "경영진의 참여",
  "estimated_minutes": 20,

  "standard": "인증기준 요구사항 문장 (원문 그대로)",
  "checkpoints": ["주요 확인사항 1", "주요 확인사항 2"],
  "explanation": ["세부 설명 핵심 1", "세부 설명 핵심 2"],
  "evidence_examples": ["증거자료 예시 1", "..."],
  "deficiency_cases": ["결함사례 1", "결함사례 2"],
  "related_laws": [],                       // 해당 항목에 있을 때만

  "quiz": [
    {
      "type": "ox",                          // "ox" | "mcq"
      "question": "문항",
      "answer": true,                         // ox: bool / mcq: 정답 index
      "choices": [],                          // mcq일 때만
      "explanation": "해설 (왜 정답인지, 원문 근거)",
      "source": "결함사례 1"                   // QA 추적용: 이 문항의 원문 출처
    }
  ]
}
```

## 규칙
- `standard`/`checkpoints`/`deficiency_cases` 는 **원문 변형 최소화** (요약 시 의미 보존).
- 모든 `quiz` 항목은 `source` 로 원문 위치를 명시 → QA가 1:1 대조.
- 항목당 퀴즈 **4~6문항** (OX 2~3 + MCQ 2~3), 세션 15~30분 목표.
- 법령 인용은 발간 시점(2023.10) 기준임을 앱에서 고지.
