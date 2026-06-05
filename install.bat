@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo MULTILINGUAL VOICE TRANSCRIBER v2.0 - KURULUM
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo HATA: Yonetici izni gerekli!
    echo.
    echo Lutfen sag tiklayip "Yonetici olarak calistir" secin.
    echo.
    pause
    exit /b 1
)

echo Adim 1: Python denetleniyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python yükleniyor...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe', 'python-installer.exe')"
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
    echo Python kuruldu.
) else (
    echo Python zaten kurulu.
)
echo.

echo Adim 2: Sanal ortam olusturuluyor...
if exist venv (
    echo Sanal ortam zaten mevcut.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo HATA: Sanal ortam olusturulamadi!
        pause
        exit /b 1
    )
    echo Sanal ortam olusturuldu.
)
echo.

echo Adim 3: Paketler yukleniyor...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo HATA: Sanal ortam etkinlestirilemedi!
    pause
    exit /b 1
)

pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo HATA: Paketler yuklenemedi!
    pause
    exit /b 1
)
echo Paketler yuklendi.
echo.

echo Adim 4: Modeller indiriliyor (5-20 dakika - internetin hizli olmali)...
mkdir models >nul 2>&1
python -c "import whisper; print('Whisper yukleniyor...'); whisper.load_model('large-v3'); print('Tamamlandi.')"
if errorlevel 1 (
    echo Uyari: Modeller indirilemedi. Internet baglantisini kontrol edin.
)
echo.

echo Adim 5: Son ayarlar yapiliiyor...
mkdir output >nul 2>&1
mkdir logs >nul 2>&1
echo.

echo.
echo ============================================================
echo KURULUM TAMAMLANDI!
echo ============================================================
echo.
echo Programi baslatmak icin:
echo.
echo 1. GUI (Tavsiye):
echo    run_gui.bat dosyasina cift tikla
echo.
echo 2. Komut Satiri:
echo    run_cli.bat dosyasina cift tikla
echo.
echo ============================================================
echo.

pause
