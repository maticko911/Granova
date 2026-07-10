@echo off
rem Granova - enkratna nastavitev (Windows). Dvoklikni to datoteko.
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python ni namescen. Prenesi ga s https://www.python.org/downloads/
    echo in pri namestitvi obkljukaj "Add Python to PATH", nato ponovi.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Pripravljam okolje ...
    python -m venv .venv
)

echo Namescam knjiznice ...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo Ponovni poskus prek zaupanja gostiteljem - nekatera omrezja prestrezajo SSL ...
    ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
)

".venv\Scripts\python.exe" -m granova.setup
pause
