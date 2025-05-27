@echo off

REM The Lineup - Quick Start Script for Windows
REM This script activates the virtual environment and starts both servers

echo 🏀 Starting The Lineup - Fantasy Basketball Draft Assistant
echo ============================================================

REM Check if we're in the right directory
if not exist "app\main.py" (
    echo ❌ Error: Please run this script from the project root directory
    echo    ^(the directory containing the 'app' folder^)
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Error: Virtual environment 'venv' not found
    echo    Please create it first with: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activation was successful
if "%VIRTUAL_ENV%"=="" (
    echo ❌ Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated: %VIRTUAL_ENV%

REM Install/update dependencies
echo 📦 Checking dependencies...
pip install -r requirements.txt --quiet

REM Run the full application
echo 🚀 Starting The Lineup...
python run_full_app.py

pause 