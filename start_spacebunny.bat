@echo off
REM SpaceBunny - A CodeRabbit GUI Utility
REM Copyright (c) 2024 Joshua Alexander (TaterFacer Software)
REM Launch script for Windows

title SpaceBunny - CodeRabbit GUI Utility

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo WARNING: Some dependencies may have failed to install.
    )
)

REM Run SpaceBunny
echo Starting SpaceBunny...
python SpaceBunny.py

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo SpaceBunny exited with an error.
    pause
)
