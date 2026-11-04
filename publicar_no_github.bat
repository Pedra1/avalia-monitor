@echo off
title Enviar Monitor para o GitHub
cd /d "%~dp0"
cls
echo ========================================================
echo        Publicar Monitor na Nuvem (GitHub Actions)
echo ========================================================
echo.
echo 1. Va em: https://github.com/new
echo 2. Crie um novo repositorio (ex: avalia-monitor)
echo    - Pode ser PUBLICO para ter minutos ilimitados gratis!
echo 3. Copie o link HTTPS gerado (ex: https://github.com/SEU_USUARIO/avalia-monitor.git)
echo.
set /p REPO_URL="Cole o link HTTPS do repositorio aqui: "

if "%REPO_URL%"=="" (
    echo [Erro] Nenhum link informado.
    pause
    exit /b
)

echo.
echo Conectando ao GitHub...
git branch -M main
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git push -u origin main

echo.
echo ========================================================
echo Pronto! Codigo enviado para o GitHub.
echo O monitor na nuvem comecara a rodar automaticamente!
echo ========================================================
echo.
pause
