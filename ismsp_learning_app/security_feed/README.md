# 뉴스·이슈 피드 파이프라인 ("오늘의 이슈")

매일 전 분야 뉴스를 RSS로 수집·분류해 `security_issues.json`(파일명은 호환상 유지)을
만들고, 앱의 **오늘의 이슈** 메뉴가 그 JSON(원격 raw URL)을 읽어 표시한다.

```
[정해진 시각]  →  ① 수집(국내 RSS)  →  ② 분야 분류 + 제목장사 필터 + 중복 제거
                                        →  ③ security_issues.json
                                        →  ④ GitHub commit (raw URL)
                                        →  ⑤ 앱 "오늘의 이슈" 메뉴가 로드
```

## 분야 (4)
정치·국제 / 사회·경제 / 스포츠·문화 / IT·과학·보안

## 출처 (계층 tier)
- **1차**: 정책브리핑(정부 보도자료) — 가장 중립적·원천
- **통신**: 연합뉴스(전체·정치·국제·경제·산업·사회·스포츠·문화) — 사실 중심
- **종합**: 한겨레·경향신문·오마이뉴스·프레시안·서울신문 — *관점은 사용자 큐레이션 영역*
- **보안**: 보안뉴스·데일리시큐·The Hacker News·BleepingComputer
> 출처마다 `perspective` 칸이 비어 있음. 임의로 성향을 단정하지 않으며, 원하시면 직접 표시·필터링할 수 있게 설계됨.

## 특징
- **분야 자동분류**: 카테고리 피드는 피드 자체 분야, 종합/정부 피드는 키워드로 분류(`DOMAIN_KEYWORDS`).
- **제목장사 필터**: 자극적 표현(충격·경악·발칵…) + 물음표/느낌표 남발 제목 자동 제외(`CLICKBAIT_WORDS`).
- **저작권**: 본문 전문 미저장(제목 + 앞부분 요약 + 링크만). 앱도 원문 링크 노출.
- 수정은 `collect.py` 상단 `SOURCES` / `DOMAIN_KEYWORDS` / `CLICKBAIT_WORDS` 만.

## 실행
```bash
pip install feedparser
python security_feed/collect.py --days 2 --max 80   # → security_feed/security_issues.json
```

## 매일 자동 — GitHub Actions (PC 불필요)
`.github/workflows/feed.yml` 이 매일 22:00 UTC(=한국 07:00) 클라우드에서 수집·커밋.
- 최초 1회: 저장소 **Settings → Actions → General → "Read and write permissions"** 켜기.
- 수동 실행: **Actions 탭 → security-feed → Run workflow**.

## 앱 연결
```bash
flutter build apk --release --dart-define=SECURITY_FEED_URL=<raw-url>
# https://raw.githubusercontent.com/help3m-hash/ismsp-learning/master/ismsp_learning_app/security_feed/security_issues.json
```
URL 미설정 시 동봉 샘플 표시. 온라인 성공 시 기기 캐시 → 오프라인도 마지막 데이터.

## JSON 스키마
```jsonc
{
  "updated_at": "...", "count": 80,
  "domains": ["정치·국제", "사회·경제", "스포츠·문화", "IT·과학·보안"],
  "issues": [
    { "id": "...", "title": "...", "summary": "...(본문 전문 아님)",
      "source": "연합뉴스", "region": "국내", "tier": "통신",
      "domain": "사회·경제", "url": "https://...",
      "published": "...", "keywords": ["..."] }
  ]
}
```

## 앱 동작
- 홈 상단 **피드 아이콘** → 오늘의 이슈.
- **분야 필터**(정치·국제/사회·경제/스포츠·문화/IT·과학·보안) + 지역(국내/해외) 필터.
- 카드: 분야 배지 + 출처·날짜, 탭 → 외부 브라우저 원문.
