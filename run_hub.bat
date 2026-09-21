@echo off
chcp 65001 > nul
title AI Automation Hub - Szerver
echo ===================================================
echo     AI AUTOMATION HUB INDITASA...
echo ===================================================
echo.
cd /d "%~dp0"
python hub_server.py
pause
