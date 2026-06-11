# tennis-records 주간 데이터 갱신을 Windows 작업 스케줄러에 등록.
# 기본: 매주 월요일 05:00. 변경하려면 아래 -At / -DaysOfWeek 수정.
# 실행:  powershell -ExecutionPolicy Bypass -File scripts\register_update_task.ps1
# 해제:  Unregister-ScheduledTask -TaskName "tennis-records-update" -Confirm:$false

$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "update_data.ps1"
$taskName = "tennis-records-update"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 5:00AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd `
  -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
  -Settings $settings -Description "tennis-records: 진행 시즌 CSV 재수신 + tennis.db 재빌드 (주간)" `
  -Force | Out-Null

Write-Output "등록 완료: '$taskName' (매주 월 05:00)"
Write-Output "확인:  Get-ScheduledTask -TaskName $taskName"
Write-Output "즉시 실행:  Start-ScheduledTask -TaskName $taskName"
