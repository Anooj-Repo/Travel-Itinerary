@echo off
echo ========================================
echo  Business Analysis Summarizer - Backend Setup
echo ========================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

echo [2/4] Activating virtual environment...
call venv\Scripts\activate
echo.

echo [3/4] Installing dependencies...
pip install -r requirement.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo [4/4] Creating .env file...
if not exist .env (
    echo HF_TOKEN=sk-9AD57oeLWenkPoca_enlUA > .env
    echo GENAI_API_KEY=sk-9AD57oeLWenkPoca_enlUA >> .env
    echo .env file created with API key
) else (
    echo .env file already exists
)
echo.

echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Press any key to exit...
pause > nul
