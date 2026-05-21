@echo off
title Mi ERP Server

cd /d "%~dp0"

set PYTHON=%cd%\venv\Scripts\python.exe

:loop

cls
echo ===============================
echo Iniciando servidor FastAPI...
echo %date% %time%
echo ===============================

netstat -ano | find ":8000" >nul

if %errorlevel%==0 (
    echo Puerto 8000 ya ocupado.
    timeout /t 5 >nul
    goto loop
)

"%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8000

echo.
echo ********************************
echo SERVIDOR DETENIDO
echo Reiniciando en 3 segundos...
echo ********************************

timeout /t 3 >nul

goto loop