@echo off
echo ==========================================
echo   EV SECURE HUB: STARTING NETWORK
echo ==========================================
echo.

:: Check for Venv
if not exist venv\Scripts\activate (
    echo [ERROR] Virtual Environment not found. 
    echo Please run 'setup.bat' first!
    pause
    exit /b
)

:: Launch App
echo [NODE] Activating Edge Security Protocol...
call venv\Scripts\activate
echo [NODE] Launching Handshake Server on http://127.0.0.1:5000
echo.
python app.py

pause
