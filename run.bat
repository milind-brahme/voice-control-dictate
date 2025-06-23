@echo off
REM Voice Control & Dictation System Launcher Script for Windows

setlocal enabledelayedexpansion

echo Voice Control ^& Dictation System
echo ==================================

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% detected

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
if not exist "venv\installed" (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo. > venv\installed
    echo Dependencies installed
) else (
    echo Dependencies up to date
)

REM Test microphone access
echo Testing microphone access...
python -c "import pyaudio; p = pyaudio.PyAudio(); print('Audio system OK'); p.terminate()" >nul 2>&1
if errorlevel 1 (
    echo Warning: Audio system test failed. Please check microphone setup.
)

REM Launch application
echo.
echo Starting Voice Control ^& Dictation System...
echo Press Ctrl+C to stop
echo.

REM Parse command line arguments
set ARGS=
:parse_args
if "%1"=="--cli" (
    set ARGS=%ARGS% --mode cli
    shift
    goto parse_args
)
if "%1"=="--dictation" (
    set ARGS=%ARGS% --dictation-mode
    shift
    goto parse_args
)
if "%1"=="--config" (
    set ARGS=%ARGS% --config %2
    shift
    shift
    goto parse_args
)
if "%1"=="--help" (
    echo Usage: %0 [OPTIONS]
    echo Options:
    echo   --cli              Run in CLI mode
    echo   --dictation        Start in dictation mode
    echo   --config FILE      Use custom config file
    echo   --help             Show this help
    pause
    exit /b 0
)

REM Run the application
python main.py %ARGS%

pause