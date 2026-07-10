@echo off
rem Zazene Granovo z vidno konzolo (za odpravljanje tezav).
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)
pause
