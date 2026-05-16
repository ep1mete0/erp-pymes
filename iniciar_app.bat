@echo off
:: ============================================================
::  iniciar_app.bat — Arranca FastAPI y abre el navegador
::  Edita las variables de la sección CONFIG antes de usar
:: ============================================================

:: ── CONFIG ──────────────────────────────────────────────────
set PYTHON=C:\Users\TU_USUARIO\AppData\Local\Programs\Python\Python311\python.exe
set PROJECT_DIR=C:\ruta\a\tu\proyecto
set APP_MODULE=main:app
set HOST=127.0.0.1
set PORT=8000
set BROWSER_DELAY=3
:: ────────────────────────────────────────────────────────────

cd /d "%PROJECT_DIR%"

:: Inicia uvicorn en segundo plano (sin ventana de consola)
start "" /B "%PYTHON%" -m uvicorn %APP_MODULE% --host %HOST% --port %PORT%

:: Espera unos segundos a que el servidor esté listo
timeout /t %BROWSER_DELAY% /nobreak >nul

:: Abre el navegador predeterminado
start "" "http://%HOST%:%PORT%"
