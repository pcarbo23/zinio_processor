@echo off
:: Zinio Media Processor - One-Click Installer Launcher
cd /d "%~dp0"
echo Starting Zinio Media Processor Installer...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Installation failed! Please check the output above.
    pause
    exit /b %errorlevel%
)
echo.
echo Installation completed successfully!
pause
