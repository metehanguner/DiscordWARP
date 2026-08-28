@echo off
title Discord WARP
cd /d "%~dp0"

:: Check for Administrative Privileges and Elevate if Needed
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d ""%~dp0"" && start """" pythonw app.py' -Verb RunAs"
    exit /b
)

start "" pythonw app.py
exit
