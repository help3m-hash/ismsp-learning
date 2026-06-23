# 보안 이슈 피드 자동 갱신: 수집 → (변경 시) commit → push
# Windows 작업 스케줄러에서 매일 호출. 첫 수동 push로 GitHub 자격증명이 캐시된 뒤엔 무인 동작.
$ErrorActionPreference = "Stop"
$repo = "C:\Users\SECUI\Desktop\claude code#2"
$rel  = "ismsp_learning_app/security_feed/security_issues.json"
Set-Location $repo

python "ismsp_learning_app\security_feed\collect.py" --days 2 --max 40

git add $rel
$changed = git status --porcelain $rel
if ($changed) {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "chore: 보안 이슈 피드 자동 갱신 $date"
    git push origin master
    Write-Output "갱신 완료: $date"
} else {
    Write-Output "변경 없음(갱신 불필요)"
}
