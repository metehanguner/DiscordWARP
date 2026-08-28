$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "Discord WARP.lnk"
$TargetVbs = Join-Path -Path $PSScriptRoot -ChildPath "run_silent.vbs"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$TargetVbs`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "Discord WARP Bypass Istemcisi"
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.Save()

# Remove old shortcut if exists
$OldShortcut = Join-Path -Path $DesktopPath -ChildPath "Cloudflare WARP.lnk"
if (Test-Path $OldShortcut) {
    Remove-Item -Force $OldShortcut
}

Write-Host "Masaustu kisayolu basariyla olusturuldu: $ShortcutPath" -ForegroundColor Green
