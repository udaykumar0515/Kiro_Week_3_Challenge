@echo off
REM Data Weaver Dashboard - Run Script
REM This script runs the dashboard using the Python 3.10 virtual environment

echo ========================================
echo   Data Weaver Dashboard Launcher
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\streamlit.exe" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run the setup first:
    echo   py -3.10 -m venv venv
    echo   .\venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting dashboard...
echo Dashboard will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run Streamlit
.\venv\Scripts\streamlit.exe run app/dashboard.py

pause
