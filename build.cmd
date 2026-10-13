@echo off
cd /d "%~dp0"
set "BUILD_PYTHON=.venv312\Scripts\python.exe"
if not exist "%BUILD_PYTHON%" set "BUILD_PYTHON=.venv\Scripts\python.exe"
"%BUILD_PYTHON%" scripts\generate_icon.py
if errorlevel 1 exit /b 1
"%BUILD_PYTHON%" -m PyInstaller --noconfirm SystemMonitor.spec
if errorlevel 1 exit /b 1
echo Built dist\SystemMonitor.exe
