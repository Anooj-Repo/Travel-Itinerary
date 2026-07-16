@echo off
echo ========================================
echo  Starting Knowledge Graph Q&A Backend
echo ========================================
echo.

if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate
echo.

echo Starting Flask server on port 5005...
python app.py

pause
