@echo off
echo Starting London Crime Backend...

REM Check if venv exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if ERRORLEVEL 1 (
        echo Failed to create virtual environment.
        echo Please make sure Python is installed and in your PATH.
        pause
        exit /b 1
    )
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if ERRORLEVEL 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install requirements if needed
if not exist venv\Scripts\pip.exe (
    echo Installing pip...
    python -m ensurepip
)

echo Installing requirements...
pip install -r requirements.txt
if ERRORLEVEL 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

REM Start the backend server
echo Starting server...
python map_api.py
if ERRORLEVEL 1 (
    echo Server exited with an error.
    pause
    exit /b 1
)

pause 