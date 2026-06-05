@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🎙️  Multilingual Voice Transcriber - Kurulum Aracı        ║
echo ║      Türkçe, Kürtçe, Arapça Sesli Yazı Dönüştürücü        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Python kontrolü
echo [1/5] Python kontrolü yapılıyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadı!
    echo 📥 Python 3.11+ indirilip kuruluyor...
    REM Python indirme linki
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe', 'python-installer.exe')"
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
    echo ✅ Python kuruldu
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo ✅ Python bulundu: !PYTHON_VERSION!
)

echo.
echo [2/5] Sanal ortam oluşturuluyor...
if exist venv (
    echo ⏭️  Sanal ortam zaten var, atlanıyor...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Sanal ortam oluşturulamadı!
        pause
        exit /b 1
    )
    echo ✅ Sanal ortam oluşturuldu
)

echo.
echo [3/5] Paketler yükleniyor...
call venv\Scripts\activate.bat
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Paketler yüklenemedi!
    pause
    exit /b 1
)
echo ✅ Paketler yüklendi

echo.
echo [4/5] Modeller indiriliyor...
echo ⏳ Bu işlem 5-15 dakika sürebilir...
mkdir models >nul 2>&1
python -m pip install --upgrade pydantic >nul 2>&1
python -c "import whisper; whisper.load_model('large-v3')"
echo ✅ Modeller indirildi

echo.
echo [5/5] Yapı dizinleri kontrol ediliyor...
mkdir output >nul 2>&1
mkdir logs >nul 2>&1
echo ✅ Dizinler oluşturuldu

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  ✅ KURULUM BAŞARILI!                                       ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║  Programı başlatmak için:                                   ║
echo ║                                                              ║
echo ║  GUI Arayüzü:      run_gui.bat                             ║
echo ║  Komut Satırı:     run_cli.bat                             ║
echo ║                                                              ║
echo ║  📝 Detaylar:      README.md'i okuyun                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

pause
