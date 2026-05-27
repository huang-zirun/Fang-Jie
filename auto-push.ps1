Start-Sleep -Seconds 1800
Set-Location 'E:\系统文件夹\Desktop\Channing\Fang-Jie'
git add -A
$status = git status --porcelain
if ($status) {
    git commit -m 'chore: auto-commit after 30min'
    git push origin main
    Write-Output 'Pushed new changes after 30 minutes'
} else {
    Write-Output 'No new changes to push after 30 minutes'
}
