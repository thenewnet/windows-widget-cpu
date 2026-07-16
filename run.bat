@echo off
REM ============================================================
REM  Float Monitor - chay widget giam sat he thong
REM  Double-click file nay de chay.
REM ============================================================
setlocal
cd /d "%~dp0"

REM Cai dat thu vien lan dau (neu thieu)
python -c "import PySide6, psutil" 2>nul
if errorlevel 1 (
    echo [*] Dang cai dat thu vien can thiet...
    python -m pip install -r requirements.txt
)

REM Chay bang pythonw de khong hien cua so console
start "" pythonw "%~dp0float_monitor.py"
endlocal
