@echo off
setlocal enabledelayedexpansion

echo.
echo MULTILINGUAL VOICE TRANSCRIBER v2.0 - SETUP
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: Admin rights required!
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Step 1: Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Installing...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe', 'python-installer.exe')"
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
    echo Python installed.
) else (
    echo Python already installed.
)
echo.

echo Step 2: Creating virtual environment...
if exist venv (
    echo Virtual environment already exists.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created.
)
echo.

echo Step 3: Installing packages...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install packages!
    pause
    exit /b 1
)
echo Packages installed.
echo.

echo Step 4: Downloading AI models (5-20 minutes)...
mkdir models >nul 2>&1
python -c "import whisper; print('Downloading Whisper...'); whisper.load_model('large-v3'); print('Done.')"
if errorlevel 1 (
    echo WARNING: Failed to download models. Check internet connection.
)
echo.

echo Step 5: Final setup...
mkdir output >nul 2>&1
mkdir logs >nul 2>&1
echo.

echo.
echo ============================================================
echo SETUP COMPLETE!
echo ============================================================
echo.
echo To start the program:
echo.
echo 1. GUI (Recommended):
echo    Double-click run_gui.bat
echo.
echo 2. Command Line:
echo    Double-click run_cli.bat
echo.
echo ============================================================
echo.

pause
