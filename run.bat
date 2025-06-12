@echo off
echo PC Builder Pro Demo Launcher
echo ===========================

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Please run: python setup.py
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate

REM Run the service
echo Starting PC Builder Pro service...
python pc_builder_service.py

REM Deactivate on exit
deactivate