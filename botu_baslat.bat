@echo off
chcp 65001 > nul
title Trendyol AI Studio Bot - Mehmet Bot
color 0A

echo ========================================================
echo       TRENDYOL AI STUDIO TELEGRAM BOTU BASLATILIYOR     
echo ========================================================
echo.

cd /d "C:\Users\Ali Onur\.gemini\antigravity\scratch\trendyol-studio-bot"

if not exist ".env" (
    echo [HATA] .env dosyasi bulunamadi!
    pause
    exit /b
)

echo [OK] Bot dinlemeye basliyor...
echo [BILGI] Bu pencere acik kaldigi surece bot Telegram'da aktiftir.
echo [BILGI] Kapatmak icin pencereyi carpisindan kapatabilirsiniz.
echo.

.\venv\Scripts\python.exe -u bot.py

pause
