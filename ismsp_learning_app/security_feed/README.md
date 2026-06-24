# 보안 이슈 피드 파이프라인

매일 보안/개인정보 이슈를 RSS로 수집·분류해 `security_issues.json`을 만들고,
앱의 **보안 이슈** 메뉴가 그 JSON(원격 raw URL)을 읽어 표시한다.

```
[정해진 시각]  →  ① 수집(국내+해외 RSS)  →  ② 키워드 분류·요약·국내/해외 구분
                                              →  ③ security_issues.json
                                              →  ④ GitHub commit (raw URL)
                                              →  ⑤ 앱 "보안 이슈" 메뉴가 raw URL 로드
```

## 1. 수집 스크립트
```bash
pip install feedparser          # 의존성(최초 1회)
python security_feed/collect.py --days 2 --max 40
# → security_feed/security_issues.json 생성
```
- 수집원 `RSS_SOURCES`: 국내(보안뉴스·데일리시큐·KISA 보호나라) + 해외(The Hacker News·BleepingComputer·Krebs·CISA). `collect.py` 상단에서 추가/삭제.
- 분류 `KEYWORD_CATEGORIES`: 6개 카테고리(ISMS-P·인증 / 개인정보보호법·규제 / 취약점·CVE·패치 / 랜섬웨어·침해사고 / 금융보안 / 클라우드·AI보안). **주제는 이 부분만 고치면 됨.**
- 심각도: 키워드 휴리스틱(높음/보통/낮음).
- **저작권**: 기사 본문 전문은 저장하지 않음(제목 + 앞부분 요약 + 링크만). 앱도 원문 링크를 함께 노출.

## 2. 매일 자동 실행 — GitHub Actions (권장, PC 불필요)
`.github/workflows/feed.yml` 이 매일 22:00 UTC(=한국 07:00) GitHub 클라우드에서
수집→커밋한다. **PC 전원과 무관**, 공개 저장소라 무료.
- 최초 1회: 저장소 **Settings → Actions → General → Workflow permissions → "Read and write permissions"** 켜기.
- 수동 실행: **Actions 탭 → security-feed → Run workflow**.

(대안) 로컬 Windows 작업 스케줄러로 `update_and_push.ps1` 매일 실행도 가능(PC 켜져 있어야 함).

## 3. 앱 연결 (GitHub raw URL)
```bash
flutter build apk --release --dart-define=SECURITY_FEED_URL=<raw-url>
# raw-url 예:
# https://raw.githubusercontent.com/help3m-hash/ismsp-learning/master/ismsp_learning_app/security_feed/security_issues.json
```
- URL 미설정 시 앱은 동봉 샘플(`app/assets/feed/security_issues.json`)을 표시.
- 온라인 로드 성공 시 기기에 캐시 → 오프라인에서도 마지막 데이터 표시.

## JSON 스키마
```jsonc
{
  "updated_at": "2026-06-24T08:50:07+09:00",
  "count": 40,
  "categories": ["ISMS-P·인증", "개인정보보호법·규제", "취약점·CVE·패치", ...],
  "issues": [
    { "id": "a1b2c3", "title": "...", "summary": "...(본문 전문 아님)",
      "source": "보안뉴스", "region": "국내", "url": "https://...",
      "published": "2026-06-24T09:00:00+09:00",
      "keywords": ["개인정보보호법·규제"], "severity": "높음" }
  ]
}
```

## 앱 측 동작
- 홈 상단 **방패 아이콘** → 보안 이슈 화면.
- **국내/해외 지역 필터** + **카테고리 칩 필터**, 심각도 배지, 카드 탭 → 외부 브라우저로 원문.
- 출처 라벨: 온라인 / 캐시 / 샘플.
