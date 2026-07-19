# Start project-local Redis for Celery. Binds 127.0.0.1:6379
# Same URL shape as live: redis://HOST:6379/0 (broker), /1 (results)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Server = Join-Path $Root "bin\redis-server.exe"
$Cli = Join-Path $Root "bin\redis-cli.exe"
$Conf = Join-Path $Root "redis.conf"
$Data = Join-Path $Root "data"

if (-not (Test-Path $Server)) {
  Write-Host "Redis binary missing - running install-redis.ps1"
  & (Join-Path $Root "install-redis.ps1")
}

$existing = Get-CimInstance Win32_Process -Filter "Name = 'redis-server.exe'" -ErrorAction SilentlyContinue
foreach ($p in $existing) {
  $path = [string]$p.ExecutablePath
  if ($path -like "*\v2\infra\redis\*") {
    Write-Host "Project Redis already running (PID $($p.ProcessId))"
    exit 0
  }
  # Kick aside any stray Redis on 6379 that is not this project
  if ($path -and ($path -notlike "*\v2\infra\redis\*")) {
    Write-Host "Stopping non-project redis-server PID $($p.ProcessId) ($path)"
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
  }
}

New-Item -ItemType Directory -Force -Path $Data | Out-Null
Write-Host "Starting project Redis: $Server"
Start-Process -FilePath $Server -ArgumentList "`"$Conf`"" -WorkingDirectory $Root -WindowStyle Minimized

$ok = $false
for ($i = 0; $i -lt 15; $i++) {
  Start-Sleep -Milliseconds 400
  try {
    $pong = & $Cli -h 127.0.0.1 -p 6379 ping 2>$null
    if ($pong -eq "PONG") { $ok = $true; break }
  } catch { }
}
if (-not $ok) {
  Write-Host "ERROR: Redis did not accept connections on 127.0.0.1:6379"
  exit 1
}
Write-Host "Redis listening on 127.0.0.1:6379"
