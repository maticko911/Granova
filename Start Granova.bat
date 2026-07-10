@echo off
rem Zazene Granovo v sistemski vrstici (brez okna konzole).
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "Granova" ".venv\Scripts\pythonw.exe" app.py
) else (
    start "Granova" pythonw app.py
)
