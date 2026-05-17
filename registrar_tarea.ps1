# ============================================================
#  registrar_tarea.ps1 — Registra iniciar_app.bat en el
#  Programador de tareas de Windows para que corra al login
#
#  INSTRUCCIONES:
#  1. Edita la variable $BatPath con la ruta real de tu .bat
#  2. Abre PowerShell como Administrador
#  3. Ejecuta:  .\registrar_tarea.ps1
# ============================================================

# ── CONFIG ───────────────────────────────────────────────────
$TaskName   = "IniciarFastAPI"
$BatPath    = "C:\Users\webma\Documents\POS\local_first\iniciar_app.bat"
$Description = "Inicia el servidor FastAPI y abre el navegador al iniciar sesión"
# ─────────────────────────────────────────────────────────────

# Verificar que el .bat existe
if (-not (Test-Path $BatPath)) {
    Write-Error "No se encontró el archivo: $BatPath"
    exit 1
}

# Eliminar tarea anterior si existe (evita duplicados)
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tarea anterior eliminada."
}

# Acción: ejecutar el .bat con cmd
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatPath`""

# Disparador: al iniciar sesión el usuario actual
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Configuración: correr con privilegios normales, no requerir contraseña visible
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Registrar la tarea
Register-ScheduledTask `
    -TaskName    $TaskName `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -Principal   $Principal `
    -Description $Description `
    -Force

Write-Host ""
Write-Host "✅ Tarea '$TaskName' registrada correctamente." -ForegroundColor Green
Write-Host "   Se ejecutará al iniciar sesión como: $env:USERNAME"
Write-Host ""
Write-Host "Para eliminarla en el futuro, ejecuta:"
Write-Host "   Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
