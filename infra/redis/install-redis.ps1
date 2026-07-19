# Download portable Redis for Windows into .\bin (first-time / CI).
# Live Linux servers should use distro Redis (apt/yum) or managed Redis —
# point REDIS_URL / CELERY_* at that host. Same DB indexes: /0 broker, /1 results.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bin = Join-Path $Root "bin"
$Zip = Join-Path $Root "Redis-x64-5.0.14.1.zip"
$Url = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"

if (Test-Path (Join-Path $Bin "redis-server.exe")) {
  Write-Host "Redis already installed at $Bin"
  exit 0
}

New-Item -ItemType Directory -Force -Path $Bin | Out-Null
Write-Host "Downloading Redis for Windows..."
Invoke-WebRequest -Uri $Url -OutFile $Zip -UseBasicParsing
Expand-Archive -Path $Zip -DestinationPath $Bin -Force
Remove-Item $Zip -Force
Write-Host "Installed: $Bin\redis-server.exe"
