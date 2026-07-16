@echo off
REM ============================================================
REM  Dong goi Float Monitor thanh file .exe chay doc lap
REM  (khong can cai Python tren may khac).
REM  Ket qua nam trong thu muc dist\FloatMonitor.exe
REM ============================================================
setlocal
cd /d "%~dp0"

echo [*] Cai dat cong cu build...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo [*] Dang dong goi...
pyinstaller --noconfirm --onefile --windowed --name FloatMonitor float_monitor.py

echo.
echo [OK] Xong! File nam tai: dist\FloatMonitor.exe
pause
endlocal
