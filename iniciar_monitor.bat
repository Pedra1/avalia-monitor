@echo off
title Monitor Instituto Avalia - Concurso 619
cd /d "%~dp0"
cls
echo ========================================================
echo    Iniciando Monitor de Publicacoes - Instituto Avalia
echo ========================================================
echo.
python monitor.py
pause
