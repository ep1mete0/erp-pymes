@echo off
set PROJECT_DIR=%~dp0
set PYTHON=%PROJECT_DIR%venv\Scripts\python.exe
set APP_MODULE=main:app
set HOST=127.0.0.1
set PORT=8000
set BROWSER_DELAY=3

cd /d "%PROJECT_DIR%"

start "" /B "%PYTHON%" -m uvicorn %APP_MODULE% --host %HOST% --port %PORT%

timeout /t %BROWSER_DELAY% /nobreak >nul

start "" "http://%HOST%:%PORT%"