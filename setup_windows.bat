@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==============================================================================
echo   🌴 Instalador y Configurador Automático - Florida 2027 (Windows 10)
echo ==============================================================================
echo.

cd /d "%~dp0"

REM 1. Detección de Python
set "PY_CMD="
py -3 --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_CMD=py -3"
) else (
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" (
    echo [ERROR] No se detectó Python 3 instalado en el sistema.
    echo Por favor descargá e instalá Python 3.10+ desde https://www.python.org/downloads/
    echo Asegurate de marcar la casilla "Add Python to PATH" durante la instalación.
    echo.
    pause
    exit /b 1
)

echo [1/6] Python detectado:
%PY_CMD% --version
echo.

REM 2. Creación del entorno virtual .venv
if not exist ".venv\Scripts\python.exe" (
    echo [2/6] Creando entorno virtual en .venv...
    %PY_CMD% -m venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Falló la creación del entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo [2/6] Entorno virtual .venv ya existe.
)
echo.

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

REM 3. Actualización de pip e instalación de dependencias
echo [3/6] Instalando dependencias desde requirements.txt...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Falló la instalación de dependencias.
    pause
    exit /b 1
)
echo.

REM 4. Instalación de navegadores de Playwright
echo [4/6] Instalando navegador Chromium para Playwright...
"%VENV_PY%" -m playwright install chromium
if !errorlevel! neq 0 (
    echo [ADVERTENCIA] Falló playwright install chromium. Si tenés Google Chrome instalado, el tracker usará Chrome real.
)
echo.

REM 5. Archivo de configuración .env
echo [5/6] Verificando archivo de configuración local .env...
if not exist ".env" (
    echo Copiando .env.example a .env...
    copy ".env.example" ".env" >nul
    echo [OK] Archivo .env creado con valores predeterminados.
) else (
    echo [OK] Archivo .env ya presente.
)
echo.

REM 6. Verificación con tests unitarios
echo [6/6] Ejecutando suite de pruebas unitarias para validar instalación...
"%VENV_PY%" -m unittest discover -s tests -v
if !errorlevel! neq 0 (
    echo.
    echo [ADVERTENCIA] Algunas pruebas fallaron. Revisá la salida superior.
) else (
    echo.
    echo ==============================================================================
    echo   ✅ ¡INSTALACIÓN COMPLETADA CON ÉXITO!
    echo ==============================================================================
    echo.
    echo Próximos pasos:
    echo   1. Abrí el archivo .env y completá tu TELEGRAM_BOT_TOKEN y CHAT_ID si querés alertas al celular.
    echo   2. Para probar una corrida manual:
    echo        run_tracker.bat
    echo   3. Para probar la alerta a Telegram:
    echo        .venv\Scripts\python.exe main.py notify-test
    echo   4. Para instalar la tarea programada automática cada 4 horas en Windows:
    echo        instalar_tarea.bat
    echo.
)

pause
endlocal

