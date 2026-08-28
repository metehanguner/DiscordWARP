@echo off
title WireGuard Servisini Tamamen Kaldir
cd /d "%~dp0"

:: Check for Administrative Privileges and Elevate if Needed
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Yonetici izni isteniyor...
    powershell -Command "Start-Process cmd -ArgumentList '/c net stop WireGuardTunnel$warp & sc.exe delete WireGuardTunnel$warp & \"C:\Program Files\WireGuard\wireguard.exe\" /uninstalltunnelservice warp & echo Servis basariyla durduruldu ve silindi! & timeout /t 3' -Verb RunAs"
    exit /b
)

net stop WireGuardTunnel$warp
sc.exe delete WireGuardTunnel$warp
"C:\Program Files\WireGuard\wireguard.exe" /uninstalltunnelservice warp
echo.
echo WireGuard tünel servisi başarıyla durduruldu ve silindi!
timeout /t 3
