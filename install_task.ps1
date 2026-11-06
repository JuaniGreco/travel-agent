# Registra el Tracker Florida 2027 en Windows Task Scheduler con frecuencia configurable y jitter aleatorio.
#
# Ejemplos de uso (en PowerShell como Administrador o usuario estándar):
#   # 1. Modo Pre-Black Friday (cada 4 horas, valor por defecto):
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1
#
#   # 2. Modo Black Friday (cada 2 horas con jitter de 10 min):
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -IntervalHours 2 -JitterMinutes 10
#
#   # 3. Modo fijo 2 veces por día (ej. 09:00 y 21:00):
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -FixedTimes -Morning 09:00 -Evening 21:00
param(
    [int]$IntervalHours = 4,
    [int]$JitterMinutes = 15,
    [switch]$FixedTimes,
    [string]$Morning = "09:00",
    [string]$Evening = "21:00",
    [string]$TaskName = "TrackerPreciosFlorida2027"
)

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $dir "run_tracker.bat"

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$bat`"" -WorkingDirectory $dir

if ($FixedTimes) {
    $t1 = New-ScheduledTaskTrigger -Daily -At $Morning -RandomDelay (New-TimeSpan -Minutes $JitterMinutes)
    $t2 = New-ScheduledTaskTrigger -Daily -At $Evening -RandomDelay (New-TimeSpan -Minutes $JitterMinutes)
    $triggers = @($t1, $t2)
    $desc = "2 veces al día ($Morning y $Evening ± $JitterMinutes min)"
} else {
    # Intervalo recurrente (ej. cada 4 horas o cada 2 horas)
    $t = New-ScheduledTaskTrigger -Daily -At "08:00"
    $t.Repetition = (New-ScheduledTaskTrigger -Once -At "08:00" -RepetitionInterval (New-TimeSpan -Hours $IntervalHours) -RepetitionDuration (New-TimeSpan -Days 1)).Repetition
    if ($JitterMinutes -gt 0) {
        $t.RandomDelay = New-TimeSpan -Minutes $JitterMinutes
    }
    $triggers = @($t)
    $desc = "cada $IntervalHours horas (inicio 08:00 ± $JitterMinutes min)"
}

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Interactive: corre con la sesión del usuario iniciada (necesario para navegador visible y perfil real).
$userId = if ($env:USERDOMAIN -and $env:USERDOMAIN -ne $env:COMPUTERNAME) { "$env:USERDOMAIN\$env:USERNAME" } else { "$env:USERNAME" }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers `
    -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "Tarea '$TaskName' registrada exitosamente: $desc."
Write-Host "Ejecutar prueba ahora: Start-ScheduledTask -TaskName $TaskName"
