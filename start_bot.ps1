# Reddit Bot PowerShell Menu Script
# Compatible with Windows PowerShell and PowerShell Core

param(
    [switch]$Service = $false,
    [switch]$Tests = $false,
    [switch]$Help = $false,
    [switch]$NoWait = $false
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: .\start_bot.ps1 [OPTIONS]" -ForegroundColor Green
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -Service    Start the bot service directly" -ForegroundColor Yellow
    Write-Host "  -Tests      Run the test suite directly" -ForegroundColor Yellow
    Write-Host "  -Help       Show this help message" -ForegroundColor Yellow
    Write-Host "  -NoWait     Don't wait for input before exiting" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "If no options are provided, an interactive menu will be shown." -ForegroundColor Green
    exit 0
}

# Function to display menu
function Show-Menu {
    Clear-Host
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "       Reddit Bot Manager" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please select an option:" -ForegroundColor Green
    Write-Host "1. Start Bot Service" -ForegroundColor Yellow
    Write-Host "2. Proceed to Tests" -ForegroundColor Yellow
    Write-Host "3. Exit" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Auto-starting Bot Service in 15 seconds..." -ForegroundColor Blue
    Write-Host "Press any key to select manually." -ForegroundColor Blue
}

# Function to start bot service
function Start-Bot {
    Write-Host ""
    Write-Host "Starting Reddit Bot..." -ForegroundColor Green
    Write-Host "==============================" -ForegroundColor Cyan
    
    # Check if Python is installed
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
            Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
            if (-not $NoWait) { Read-Host "Press Enter to exit" }
            exit 1
        }
        Write-Host "Found: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Python is not installed or not accessible" -ForegroundColor Red
        if (-not $NoWait) { Read-Host "Press Enter to exit" }
        exit 1
    }
    
    # Navigate to script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir
    Write-Host "Working directory: $scriptDir" -ForegroundColor Cyan
    
    # Check if virtual environment exists
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
            if (-not $NoWait) { Read-Host "Press Enter to exit" }
            exit 1
        }
    }
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    } elseif (Test-Path "venv\Scripts\activate.bat") {
        & cmd /c "venv\Scripts\activate.bat && set"
    } else {
        Write-Host "ERROR: Could not find virtual environment activation script" -ForegroundColor Red
        if (-not $NoWait) { Read-Host "Press Enter to exit" }
        exit 1
    }
    
    # Check if .env file exists
    if (-not (Test-Path "config\.env")) {
        Write-Host "ERROR: Configuration file config\.env not found!" -ForegroundColor Red
        Write-Host "Please copy config\.env.example to config\.env and configure your credentials" -ForegroundColor Yellow
        if (-not $NoWait) { Read-Host "Press Enter to exit" }
        exit 1
    }
    
    # Install/update dependencies
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip | Out-Host
    python -m pip install -r requirements.txt | Out-Host
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        if (-not $NoWait) { Read-Host "Press Enter to exit" }
        exit 1
    }
    
    # Create necessary directories
    $directories = @("logs", "database", "templates")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
            Write-Host "Created directory: $dir" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "Starting Reddit Bot with Web UI..." -ForegroundColor Green
    Write-Host "Web UI will be available at: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Yellow
    Write-Host ""
    
    # Start the bot
    try {
        python src\main.py
    } catch {
        Write-Host "ERROR: Failed to start bot - $_" -ForegroundColor Red
        if (-not $NoWait) { Read-Host "Press Enter to exit" }
        exit 1
    }
    
    Write-Host ""
    Write-Host "Bot stopped." -ForegroundColor Yellow
}

# Function to run tests
function Start-Tests {
    Write-Host ""
    Write-Host "Running Reddit Bot Tests..." -ForegroundColor Green
    Write-Host "==============================" -ForegroundColor Cyan
    
    # Check if Python is installed
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
            return
        }
    } catch {
        Write-Host "ERROR: Python is not installed or not accessible" -ForegroundColor Red
        return
    }
    
    # Navigate to script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv venv
    }
    
    # Activate virtual environment
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    }
    
    # Install dependencies
    Write-Host "Installing test dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt | Out-Null
    
    # Run tests
    if (Test-Path "tests\run_tests.py") {
        python tests\run_tests.py
    } else {
        Write-Host "ERROR: Test suite not found" -ForegroundColor Red
        Write-Host "Please ensure tests\run_tests.py exists" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Press Enter to return to menu..." -ForegroundColor Blue
    Read-Host
}

# Function to read input with timeout and countdown
function Read-WithTimeout {
    param(
        [int]$TimeoutSeconds = 15
    )
    
    Write-Host "Auto-starting Bot Service in $TimeoutSeconds seconds..." -ForegroundColor Cyan
    Write-Host "Press 1, 2, or 3 to select an option:" -ForegroundColor Cyan
    
    for ($i = $TimeoutSeconds; $i -gt 0; $i--) {
        Write-Host "`rStarting in $("{0,2}" -f $i) seconds... (Press 1, 2, or 3)" -ForegroundColor Cyan -NoNewline
        
        # Check for key press with 1-second timeout
        $timespan = New-TimeSpan -Seconds 1
        $timeout = (Get-Date).Add($timespan)
        
        while ((Get-Date) -lt $timeout) {
            if ([Console]::KeyAvailable) {
                $keyInfo = [Console]::ReadKey($true)
                $choice = $keyInfo.KeyChar
                
                Write-Host ""  # New line
                
                if ($choice -match '[123]') {
                    return $choice
                } else {
                    Write-Host "Invalid choice '$choice'. Please press 1, 2, or 3" -ForegroundColor Red
                    # Continue countdown
                    break
                }
            }
            Start-Sleep -Milliseconds 50
        }
    }
    
    Write-Host ""  # New line
    Write-Host "Timeout reached. Starting Bot Service..." -ForegroundColor Blue
    return "1"  # Default to option 1
}

# Main function
function Main {
    # Handle command-line arguments
    if ($Service) {
        Start-Bot
        return
    }
    
    if ($Tests) {
        Start-Tests
        return
    }
    
    # Interactive menu
    while ($true) {
        Show-Menu
        
        $choice = Read-WithTimeout -TimeoutSeconds 15
        
        switch ($choice) {
            "1" {
                Start-Bot
                break
            }
            "2" {
                Start-Tests
            }
            "3" {
                Write-Host "Goodbye!" -ForegroundColor Green
                exit 0
            }
            default {
                # This should not happen with the new timeout function
                Write-Host "Unexpected error. Starting Bot Service..." -ForegroundColor Red
                Start-Sleep -Seconds 1
                Start-Bot
                break
            }
        }
    }
}

# Run main function
Main

if (-not $NoWait) {
    Read-Host "Press Enter to exit"
}