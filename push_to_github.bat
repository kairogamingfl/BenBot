@echo off
title Push BEN Bot to GitHub
color 0A
echo ==============================================================
echo             PUSH BEN BOT TO GITHUB REPOSITORY
echo          Target: https://github.com/kairogamingfl/BenBot
echo ==============================================================
echo.
echo Notice: Your Discord Bot Token (.env) is automatically
echo protected and will NOT be uploaded to GitHub.
echo.
python push_to_github.py %*
echo.
pause
