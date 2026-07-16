# ============================================================================
#  Float Monitor - Go cai dat
#  Chay:  irm https://raw.githubusercontent.com/thenewnet/windows-widget-cpu/main/uninstall.ps1 | iex
# ============================================================================

$ErrorActionPreference = 'SilentlyContinue'

$AppName    = 'FloatMonitor'
$InstallDir = Join-Path $env:LOCALAPPDATA $AppName
$ConfigDir  = Join-Path $env:APPDATA $AppName

Write-Host "[*] Dang go cai dat Float Monitor..." -ForegroundColor Cyan

# Dung tien trinh dang chay
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -match 'float_monitor\.py' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# Xoa shortcut
Remove-Item (Join-Path ([Environment]::GetFolderPath('Programs')) 'Float Monitor.lnk') -Force
Remove-Item (Join-Path ([Environment]::GetFolderPath('Desktop'))  'Float Monitor.lnk') -Force

# Xoa muc khoi dong cung Windows (neu co)
Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' `
    -Name $AppName -Force

# Xoa thu muc cai dat va cau hinh
Remove-Item -Recurse -Force $InstallDir
Remove-Item -Recurse -Force $ConfigDir

Write-Host "[OK] Da go cai dat xong." -ForegroundColor Green
