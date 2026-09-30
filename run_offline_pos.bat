@echo off
cd /d "%~dp0"

where python >nul 2>nul
if not errorlevel 1 (
    python offline_pos.py
    exit /b
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 offline_pos.py
    exit /b
)

if exist "C:\python314\python.exe" (
    "C:\python314\python.exe" offline_pos.py
    exit /b
)

echo Python 3.10 or newer with Tkinter is required. Install Python and run this file again.
pause