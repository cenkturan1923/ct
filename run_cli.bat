@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo .
echo 🎙️  Multilingual Voice Transcriber - Command Line
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

REM Yardım mesajı
echo Kullanım:
echo   python app.py --audio "path\to\audio.mp3" [seçenekler]
echo.
echo Seçenekler:
echo   --language {tr|ckb|kmr|ar|auto}  Dil (varsayılan: auto)
echo   --speaker-diarization {true|false}  Kişi ayrımı (varsayılan: true)
echo   --output "path/to/output"  Çıkış dosyası
echo.
echo Örnekler:
echo   python app.py --audio speech.mp3
echo   python app.py --audio speech.wav --language tr
echo   python app.py --audio speech.mp3 --speaker-diarization false
echo.

REM Eğer parametre verilmişse komut satırına git
if "%1"=="" (
    cmd /k
) else (
    python app.py %*
    pause
)
