@echo off
title Teste de Notificacoes - Monitor Avalia
cd /d "%~dp0"
cls
echo ========================================================
echo          Disparando Notificacao de Teste...
echo ========================================================
echo.
python monitor.py --test
echo.
pause
