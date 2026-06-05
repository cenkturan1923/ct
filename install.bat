@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  Multilingual Voice Transcriber v2.0 - KURULUM
echo ============================================================
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo HATA: Yönetici izni gerekli!
    pause
    exit /b 1
)

echo [1/5] Python denetleniyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python yükleniyor...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe', 'python-installer.exe')"
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
)

echo [2/5] Sanal ortam olusturuluyor...
if not exist venv (
    python -m venv venv
)

echo [3/5] Paketler yukleniyor...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

echo [4/5] Modeller indiriliyor...
mkdir models
python -c "import whisper; whisper.load_model('large-v3')"

echo [5/5] Son ayarlar...
mkdir output
mkdir logs

echo.
echo KURULUM TAMAMLANDI!
echo.
echo Programi baslatmak icin:
echo   - run_gui.bat (GUI)
echo   - run_cli.bat (Komut satiri)
echo.
pause
