@echo off
title DiscordWARP EXE Olusturucu
echo =======================================
echo    DiscordWARP EXE Paketleniyor...
echo =======================================

python -m PyInstaller --noconfirm --onefile --windowed --uac-admin --name "DiscordWARP" --icon "icon.ico" --add-binary "wireguard-installer.exe;." --add-data "icon.ico;." --add-data "icon.png;." --collect-all customtkinter --hidden-import "pystray._win32" app.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================
    echo [BASARILI] DiscordWARP.exe "dist" klasorunde olusturuldu!
    echo Ozel simge (icon) ve WireGuard yukleyicisi EXE icine gomuldu.
    echo Baska bilgisayara sadece dist/DiscordWARP.exe dosyasini atmaniz yeterlidir!
    echo =======================================
) else (
    echo.
    echo [HATA] EXE olusturulurken hata meydana geldi.
)
pause
