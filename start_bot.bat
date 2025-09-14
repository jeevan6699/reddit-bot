@echo off
setlocal enabledelayedexpansion

REM Parse command-line arguments
set SKIP_MENU=false
set ACTION=

:parse_args
if "%~1"=="" goto check_args
if /i "%~1"=="/service" (
    set SKIP_MENU=true
    set ACTION=service
    shift
    goto parse_args
)
if /i "%~1"=="/tests" (
    set SKIP_MENU=true
    set ACTION=tests
    shift
    goto parse_args
)
if /i "%~1"=="/help" (
    echo Usage: %0 [OPTIONS]
    echo.
    echo Options:
    echo   /service    Start the bot service directly
    echo   /tests      Run the test suite directly
    echo   /help       Show this help message
    echo.
    echo If no options are provided, an interactive menu will be shown.
    exit /b 0
)
if /i "%~1"=="/?" (
    echo Usage: %0 [OPTIONS]
    echo.
    echo Options:
    echo   /service    Start the bot service directly
    echo   /tests      Run the test suite directly
    echo   /help       Show this help message
    echo.
    echo If no options are provided, an interactive menu will be shown.
    exit /b 0
)
echo Unknown option: %~1
echo Use /help for usage information
exit /b 1

:check_args
REM Handle command-line arguments
if "%SKIP_MENU%"=="true" (
    if "%ACTION%"=="service" goto start_bot
    if "%ACTION%"=="tests" goto run_tests
)

:menu
cls
echo ======================================
echo        Reddit Bot Manager
echo ======================================
echo.
echo Please select an option:
echo 1. Start Bot Service
echo 2. Proceed to Tests  
echo 3. Exit
echo.

REM Interactive timeout with choice
echo Auto-starting Bot Service in 15 seconds...
echo Press 1, 2, or 3 now to select an option, or wait for auto-start:

choice /c 123 /t 15 /d 1 /m "Select option (1=Start Bot, 2=Run Tests, 3=Exit)"
if errorlevel 3 goto exit_script
if errorlevel 2 goto run_tests
if errorlevel 1 goto start_bot

:start_bot
cls
echo Starting Reddit Bot...
echo ==============================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: %PYTHON_VERSION%

REM Navigate to script directory
cd /d "%~dp0"
echo Working directory: %CD%

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: Could not find virtual environment activation script
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist "config\.env" (
    echo ERROR: Configuration file config\.env not found!
    echo Please copy config\.env.example to config\.env and configure your credentials
    pause
    exit /b 1
)

REM Install/update dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing...
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "database" mkdir database
if not exist "templates" mkdir templates

echo.
echo Starting Reddit Bot with Web UI...
echo Web UI will be available at: http://localhost:5000
echo Press Ctrl+C to stop the bot
echo.

REM Start the bot
python src\main.py
if errorlevel 1 (
    echo ERROR: Failed to start bot
    pause
    exit /b 1
)

echo.
echo Bot stopped.
goto menu

:run_tests
cls
echo Running Test Suite...
echo ==============================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    goto menu
)

REM Navigate to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        goto menu
    )
)

REM Activate virtual environment
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: Could not find virtual environment activation script
    pause
    goto menu
)

REM Install test dependencies
echo Installing test dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install pytest pytest-asyncio pytest-mock >nul 2>&1

REM Run tests
echo.
echo Running tests...
python -m pytest tests/ -v
echo.
echo Test run completed.
pause
goto menu

:exit_script
echo Goodbye!
exit /b 0