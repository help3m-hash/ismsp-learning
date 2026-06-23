# 보안 이슈 피드 자동 갱신: 수집 → (변경 시) commit → push
# Windows 작업 스케줄러에서 매일 호출. 첫 수동 push로 GitHub 자격증명이 캐시된 뒤엔 무인 동작.
# 주의: git은 정상 진행 메시지를 stderr로 출력하므로 $ErrorActionPreference=Stop 을 쓰지 않고
#       $LASTEXITCODE로 실제 성공 여부를 판단한다.
$repo = "C:\Users\SECUI\Desktop\claude code#2"
$rel  = "ismsp_learning_app/security_feed/security_issues.json"
Set-Location $repo

python "ismsp_learning_app\security_feed\collect.py" --days 2 --max 40
if ($LASTEXITCODE -ne 0) { Write-Output "수집 실패(exit $LASTEXITCODE)"; exit 1 }

git add $rel
$changed = git status --porcelain $rel
if ($changed) {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "chore: 보안 이슈 피드 자동 갱신 $date" | Out-Null
    git push origin master 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output "갱신·푸시 완료: $date" }
    else { Write-Output "푸시 실패(exit $LASTEXITCODE)"; exit 1 }
} else {
    Write-Output "변경 없음(갱신 불필요)"
}
