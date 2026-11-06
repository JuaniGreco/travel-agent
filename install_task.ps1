# Registra el Tracker Florida 2027 en Windows Task Scheduler: 2 veces por día con jitter aleatorio.
# Uso (PowerShell, en la carpeta del proyecto):
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -Morning 08:30 -Evening 20:30
param(
    [string]$Morning = "09:00",
    [string]$Evening = "21:00",
    [int]$JitterMinutes = 20,
    [string]$TaskName = "TrackerPreciosFlorida2027"
)

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $dir "run_tracker.bat"

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$bat`"" -WorkingDirectory $dir
$t1 = New-ScheduledTaskTrigger -Daily -At $Morning -RandomDelay (New-TimeSpan -Minutes $JitterMinutes)
$t2 = New-ScheduledTaskTrigger -Daily -At $Evening -RandomDelay (New-TimeSpan -Minutes $JitterMinutes)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)
# Interactive: corre con la sesión del usuario iniciada (necesario para navegador visible).
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($t1, $t2) `
    -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "Tarea '$TaskName' registrada: $Morning y $Evening (+0-$JitterMinutes min)."
Write-Host "Probar ahora:  Start-ScheduledTask -TaskName $TaskName"

