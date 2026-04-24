@echo off
echo ==========================================
echo   EV SECURE HUB: INITIAL SETUP
echo ==========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ and add it to PATH.
    pause
    exit /b
)

:: Create Virtual Environment
echo [1/3] Creating Virtual Environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b
)

:: Install Dependencies
echo [2/3] Installing Security and Web Packages...
call venv\Scripts\activate
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed. Check your internet connection.
    pause
    exit /b
)

:: Initialize Database Simulation
echo [3/3] Initializing Secure Ledger...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database Handshake Successful.')"

echo.
echo ==========================================
echo   SETUP COMPLETE! 
echo   Run 'run_all.bat' to start the network.
echo ==========================================
pause
