@echo off
setlocal

REM Always run from the folder that contains this batch file.
cd /d "%~dp0"

echo.
echo Setting up Django E-Commerce Store...

REM Create the virtual environment only on the first run.
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create the virtual environment. Check that Python is installed.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call "venv\Scripts\activate.bat"

echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install the required packages.
    pause
    exit /b 1
)

echo Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo Database migration failed.
    pause
    exit /b 1
)

echo Creating local admin account if needed...
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@gmail.com','12345')"

echo.
echo Starting the server...
echo Open http://127.0.0.1:8000/ in your browser.
echo Press Ctrl+C to stop the server.
echo.
python manage.py runserver 0.0.0.0:8000
