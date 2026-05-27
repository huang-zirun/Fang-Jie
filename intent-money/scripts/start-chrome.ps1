$chromePaths = @(
    "$env:PROGRAMFILES\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chrome = $null
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chrome = $path
        break
    }
}

if (-not $chrome) {
    Write-Error "Chrome not found"
    exit 1
}

$userDataDir = "$env:USERPROFILE\.intent-money\chrome-user-data"
if (-not (Test-Path $userDataDir)) {
    New-Item -ItemType Directory -Path $userDataDir -Force | Out-Null
}

Start-Process $chrome -ArgumentList "--remote-debugging-port=9222","--user-data-dir=$userDataDir","--no-first-run","--no-default-browser-check"

Write-Host "Chrome launched with remote debugging on port 9222"
Write-Host "CDP debug URL: http://localhost:9222"
