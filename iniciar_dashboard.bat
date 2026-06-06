@echo off
chcp 65001 >nul
echo ========================================
echo Iniciando Dashboard Trafico Medellin
echo ========================================
echo.

REM Intentar iniciar MySQL en WSL (si existe)
where wsl >nul 2>&1
if %errorlevel% equ 0 (
    echo 1. Iniciando MySQL en WSL...
    wsl -d Ubuntu -u root -- bash -c "service mysql start" >nul 2>&1
    if %errorlevel% equ 0 (
        echo    MySQL listo.
    ) else (
        echo    [WARN] No se pudo iniciar MySQL. Intentando con distro por defecto...
        wsl -u root -- bash -c "service mysql start" >nul 2>&1
    )
) else (
    echo [INFO] WSL no detectado. El dashboard usara el modo Parquet (local).
)
echo.

echo 2. Iniciando Streamlit...
streamlit run dashboard\app.py
echo.
pause
