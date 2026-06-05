@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo .
echo 🎙️  Multilingual Voice Transcriber - GUI
echo.

REM Sanal ortam kontrolü
if not exist venv (
    echo ❌ Sanal ortam bulunamadı!
    echo Lütfen önce setup.bat'ı çalıştırın.
    pause
    exit /b 1
)

REM Sanal ortamı etkinleştir
call venv\Scripts\activate.bat

REM GUI'yi başlat
python gui.py
