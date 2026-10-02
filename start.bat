@echo off
title BEN Discord Bot Launcher
color 0B
echo ==============================================================
echo                 STARTING BEN DISCORD BOT
echo           Engineered with Transparent Embed UI (#2B2D31)
echo ==============================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from python.org and check "Add to PATH".
    echo.
    pause
    exit /b
)

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    echo [*] Installing required packages...
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

:: Run the bot
echo [*] Launching BEN...
python main.py

echo.
echo [!] Bot process stopped.
pause
