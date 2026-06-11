# tennis-records 데이터 자동 갱신 스크립트
# - 진행 중인 시즌(올해)과 직전 연도 CSV 를 다시 받아 tennis.db 재빌드
# - SQLite 쓰기 락을 피하려 파이썬 프로세스를 먼저 정리 (실행 중인 API 서버 포함)
# 수동 실행:  powershell -ExecutionPolicy Bypass -File scripts\update_data.ps1
# 스케줄:     register_update_task.ps1 가 주간 작업으로 등록

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot          # repo 루트
$backend = Join-Path $root "backend"
$py = Join-Path $backend ".venv\Scripts\python.exe"
$log = Join-Path $root "data\update.log"

function Log($msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
  $line | Tee-Object -FilePath $log -Append
}

if (-not (Test-Path $py)) { Log "ERROR: venv 파이썬 없음: $py"; exit 1 }

$year = (Get-Date).Year
$start = $year - 1                                # 직전 연도까지 재수신(늦은 결과 보정)

Log "=== 업데이트 시작 (fetch $start-$year) ==="

# 1) DB 락 방지 — 파이썬 프로세스 종료
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$env:PYTHONIOENCODING = "utf-8"
Push-Location $backend
try {
  Log "fetch_sources..."
  & $py -m etl.fetch_sources --start $start --end $year 2>&1 | Tee-Object -FilePath $log -Append
  Log "build_db..."
  & $py -m etl.build_db 2>&1 | Select-Object -Last 4 | Tee-Object -FilePath $log -Append
  Log "build_olympics..."
  & $py -m etl.build_olympics 2>&1 | Select-Object -Last 1 | Tee-Object -FilePath $log -Append
  Log "build_rankings..."
  & $py -m etl.build_rankings 2>&1 | Select-Object -Last 1 | Tee-Object -FilePath $log -Append
  Log "=== 업데이트 완료 ==="
}
catch {
  Log "ERROR: $_"
  exit 1
}
finally {
  Pop-Location
}
