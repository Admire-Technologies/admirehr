@echo off
REM Development startup script for Admire HRMS backend (Windows)

echo Starting Admire HRMS Development Environment...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create development data
echo Setting up development data...
python scripts\setup_dev.py

REM Start development server
echo Starting Django development server...
python manage.py runserver 0.0.0.0:8000