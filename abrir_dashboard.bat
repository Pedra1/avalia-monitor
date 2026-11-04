@echo off
title Dashboard Visual - Monitor Instituto Avalia
cd /d "%~dp0"
cls
echo Iniciando Painel Web...
streamlit run dashboard.py
pause
