# 보안 이슈 피드 파이프라인

매일 보안 뉴스/취약점을 수집·분류해 `security_issues.json`을 만들고, 앱의 **보안 이슈** 메뉴가 그 JSON(원격 raw URL)을 읽어 표시한다.

```
[정해진 시각]  →  ① 수집(RSS+NVD)  →  ② 분류·요약  →  ③ security_issues.json
                                                          →  ④ GitHub commit(raw URL)
                                                          →  ⑤ 앱 "보안 이슈" 메뉴가 raw URL 로드
```

## 1. 수집 스크립트
```bash
python security_feed/collect.py --days 2 --max 40
# → security_feed/security_issues.json 생성
```
- 수집원: `RSS_FEEDS`(보안뉴스·데일리시큐 등) + NVD CVE API. 피드는 `collect.py` 상단에서 추가/삭제.
- 분류: `keywords.json`의 태그별 `match` 키워드로 자동 태깅. **주제는 이 파일만 고치면 됨.**
- 심각도: CVE는 CVSS 기준(긴급/높음/중간/낮음), RSS는 키워드 휴리스틱.
- 요약: 원문 복제를 피하려 제목 기반 간결 요약. (Claude Code 루틴으로 돌리면 summary를 패러프레이즈로 개선 가능)

## 2. 매일 자동 실행 (택1)
**(A) Windows 작업 스케줄러** — 매일 07:00 실행 예시
```powershell
$action  = New-ScheduledTaskAction -Execute "python" `
  -Argument "`"C:\...\ismsp_learning_app\security_feed\collect.py`" --days 2" `
  -WorkingDirectory "C:\...\ismsp_learning_app"
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00am
Register-ScheduledTask -TaskName "ISMSP-SecurityFeed" -Action $action -Trigger $trigger
```
그 다음 GitHub에 commit·push 하는 단계(아래 3)를 같은 스크립트/배치에 이어 붙인다.

**(B) Claude Code 루틴(cron)** — `/schedule`로 매일 아침 다음을 실행하도록 등록:
> "security_feed/collect.py 실행 → 생성된 security_issues.json의 각 summary를 한국어 한 줄로 자연스럽게 재작성(원문 복제 금지) → git add·commit·push"

## 3. GitHub 호스팅 + 앱 연결
1. (공개 또는 비공개) 저장소 생성 후 이 프로젝트를 push.
2. `security_feed/security_issues.json`의 **raw URL** 확인:
   `https://raw.githubusercontent.com/<user>/<repo>/<branch>/ismsp_learning_app/security_feed/security_issues.json`
3. 앱을 그 URL로 빌드:
   ```bash
   flutter build apk --release --dart-define=SECURITY_FEED_URL=<raw-url>
   ```
   - URL 미설정 시 앱은 **동봉 샘플**(`assets/feed/security_issues.json`)을 표시한다.
   - 한 번 온라인 로드에 성공하면 기기에 캐시되어 오프라인에서도 마지막 데이터를 본다.

> 비공개 저장소의 raw URL은 토큰이 필요해 앱에서 직접 못 읽는다. 개인용으로 간단히 하려면 **공개 저장소** 또는 GitHub Pages/Gist(raw) 권장.

## JSON 스키마
```jsonc
{
  "updated_at": "2026-06-23T07:00:00+09:00",
  "count": 30,
  "issues": [
    { "id": "20260623-001", "title": "...", "summary": "...", "source": "KISA",
      "url": "https://...", "published": "2026-06-23",
      "keywords": ["취약점·CVE"], "severity": "높음" }
  ]
}
```

## 앱 측 동작
- 홈 상단 **방패 아이콘** → 보안 이슈 화면.
- 키워드 칩으로 필터, 심각도 배지, 카드 탭 → 외부 브라우저로 원문 링크.
- 출처 라벨: 온라인 / 캐시 / 샘플.
