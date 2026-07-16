# ============================================================================
#  Float Monitor - Trinh cai dat 1 dong lenh cho Windows
#
#  Chay bang 1 lenh duy nhat (PowerShell):
#    irm https://raw.githubusercontent.com/thenewnet/windows-widget-cpu/main/install.ps1 | iex
#
#  Script se:
#    - Tai float_monitor.py tu GitHub (khong can clone repo)
#    - Tao moi truong Python rieng (venv) va cai PySide6 + psutil
#    - Tao shortcut o Start Menu va Desktop
#    - Chay widget ngay lap tuc
# ============================================================================

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RepoRaw    = 'https://raw.githubusercontent.com/thenewnet/windows-widget-cpu/main'
$AppName    = 'FloatMonitor'
$InstallDir = Join-Path $env:LOCALAPPDATA $AppName
$ScriptPath = Join-Path $InstallDir 'float_monitor.py'
$VenvDir    = Join-Path $InstallDir 'venv'

function Info($m)  { Write-Host "[*] $m" -ForegroundColor Cyan }
function Ok($m)    { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m)  { Write-Host "[!] $m" -ForegroundColor Yellow }
function Fail($m)  { Write-Host "[X] $m" -ForegroundColor Red }

Write-Host ""
Write-Host "  Float Monitor - Widget giam sat he thong" -ForegroundColor White
Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# --- 1. Tim Python -------------------------------------------------------- #
function Find-PythonBase {
    $candidates = @(
        ,@('py', '-3')
        ,@('python')
        ,@('python3')
    )
    foreach ($cand in $candidates) {
        $exe = $cand[0]
        $pre = if ($cand.Count -gt 1) { $cand[1..($cand.Count - 1)] } else { @() }
        try {
            $out = & $exe @pre -c "import sys; print(sys.executable)" 2>$null
        } catch { continue }
        if ($LASTEXITCODE -eq 0 -and $out) { return ($out | Select-Object -First 1).Trim() }
    }
    return $null
}

Info "Dang kiem tra Python..."
$python = Find-PythonBase

if (-not $python) {
    Warn "Khong tim thay Python. Dang thu cai qua winget..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            winget install -e --id Python.Python.3.12 --source winget `
                --accept-package-agreements --accept-source-agreements | Out-Null
        } catch { }
        # Nap lai PATH cho phien hien tai
        $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                    [Environment]::GetEnvironmentVariable('Path', 'User')
        $python = Find-PythonBase
    }
}

if (-not $python) {
    Fail "Chua co Python. Vui long cai Python 3.9+ tu https://www.python.org/downloads/"
    Fail "(nho tick 'Add Python to PATH'), mo lai PowerShell roi chay lenh nay lai."
    return
}
Ok "Da tim thay Python: $python"

# --- 2. Tao thu muc & tai ma nguon ---------------------------------------- #
Info "Thu muc cai dat: $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Info "Dang tai float_monitor.py tu GitHub..."
Invoke-WebRequest -UseBasicParsing -Uri "$RepoRaw/float_monitor.py" -OutFile $ScriptPath
Ok "Da tai ma nguon."

# --- 3. Dung phien ban dang chay (neu co) --------------------------------- #
try {
    Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
        Where-Object { $_.CommandLine -and $_.CommandLine -match 'float_monitor\.py' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
} catch { }

# --- 4. Tao venv & cai thu vien ------------------------------------------- #
$VenvPythonw = Join-Path $VenvDir 'Scripts\pythonw.exe'
$VenvPython  = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    Info "Dang tao moi truong Python rieng (venv)..."
    & $python -m venv $VenvDir
}

Info "Dang cai thu vien (PySide6, psutil) - lan dau co the mat vai phut..."
& $VenvPython -m pip install --upgrade pip     | Out-Null
& $VenvPython -m pip install PySide6 psutil
if ($LASTEXITCODE -ne 0) {
    Fail "Cai thu vien that bai. Kiem tra ket noi mang roi thu lai."
    return
}
Ok "Da cai xong thu vien."

# --- 5. Tao shortcut ------------------------------------------------------ #
function New-Shortcut($LinkPath) {
    $sh = New-Object -ComObject WScript.Shell
    $lnk = $sh.CreateShortcut($LinkPath)
    $lnk.TargetPath       = $VenvPythonw
    $lnk.Arguments        = '"' + $ScriptPath + '"'
    $lnk.WorkingDirectory = $InstallDir
    $lnk.IconLocation     = $VenvPythonw
    $lnk.Description       = 'Float Monitor - Widget giam sat he thong'
    $lnk.Save()
}

try {
    $startMenu = [Environment]::GetFolderPath('Programs')
    New-Shortcut (Join-Path $startMenu 'Float Monitor.lnk')
    New-Shortcut (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Float Monitor.lnk')
    Ok "Da tao shortcut o Start Menu va Desktop."
} catch {
    Warn "Khong tao duoc shortcut (bo qua)."
}

# --- 6. Chay ngay --------------------------------------------------------- #
Info "Dang khoi dong Float Monitor..."
Start-Process -FilePath $VenvPythonw -ArgumentList "`"$ScriptPath`"" -WorkingDirectory $InstallDir

Write-Host ""
Ok "Cai dat hoan tat!"
Write-Host ""
Write-Host "  - Widget da hien o goc tren ben phai man hinh - keo toi cho ban thich." -ForegroundColor Gray
Write-Host "  - Chuot phai vao widget de doi mau, do trong suot, khoi dong cung Windows..." -ForegroundColor Gray
Write-Host "  - Mo lai bat cu luc nao qua shortcut 'Float Monitor'." -ForegroundColor Gray
Write-Host "  - Go cai dat:" -ForegroundColor Gray
Write-Host "      irm $RepoRaw/uninstall.ps1 | iex" -ForegroundColor DarkGray
Write-Host ""
