# Stop project-local Redis under v2/infra/redis only
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$stopped = 0
$existing = Get-CimInstance Win32_Process -Filter "Name = 'redis-server.exe'" -ErrorAction SilentlyContinue
foreach ($p in $existing) {
  $path = [string]$p.ExecutablePath
  if ($path -like "*\v2\infra\redis\*") {
    Write-Host "Stopping project Redis PID $($p.ProcessId)"
    Stop-Process -Id $p.ProcessId -Force
    $stopped++
  }
}
if ($stopped -eq 0) { Write-Host "No project redis-server found under v2\infra\redis." }
