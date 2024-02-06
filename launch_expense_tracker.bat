@echo off

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Installing Python...
    REM Install Python
    start /wait "" "https://www.python.org/ftp/python/3.10.2/python-3.10.2-amd64.exe" /passive
    REM Wait for Python installation to complete
    timeout /t 30
)

REM Activate virtual environment if exists
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

REM Start Django server
echo Starting Django server...
start /min "" python manage.py runserver

REM Wait for Django server to start
timeout /t 10

REM Start Electron application
echo Starting Electron application...
start /min "" npm run expense

echo All processes started successfully.
