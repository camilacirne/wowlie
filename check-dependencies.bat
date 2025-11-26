@echo off
title WowLie Wallet - Verificacao de Dependencias

echo ========================================
echo   WowLie Wallet - Verificacao
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo Certifique-se de marcar a opcao:
    echo "Add Python to PATH" durante a instalacao
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version

REM Verificar Streamlit
python -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Streamlit nao encontrado
    echo.
    echo Instalando dependencias...
    echo.
    
    REM Tentar instalar
    python -m pip install streamlit btclib requests qrcode Pillow cryptography rich
    
    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao instalar dependencias!
        echo.
        echo Execute manualmente:
        echo pip install streamlit btclib requests qrcode Pillow cryptography rich
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo [OK] Dependencias instaladas!
) else (
    echo [OK] Streamlit encontrado
)

echo.
echo ========================================
echo   Tudo pronto!
echo ========================================
echo.

exit /b 0
