@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

set "VENV_DIR=%PROJECT_DIR%venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "ACTIVATE_BAT=%VENV_DIR%\Scripts\activate.bat"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    if exist "%VENV_DIR%" (
        rmdir /s /q "%VENV_DIR%"
    )
    py -3 -m venv "%VENV_DIR%"
)

if not exist "%PYTHON_EXE%" (
    echo Failed to create virtual environment.
    exit /b 1
)

if not exist "%ACTIVATE_BAT%" (
    echo Missing activation script inside the virtual environment.
    exit /b 1
)

echo Activating virtual environment...
call "%ACTIVATE_BAT%"

if errorlevel 1 (
    echo Failed to activate the virtual environment.
    exit /b 1
)

echo Installing dependencies into the virtual environment...
python -m pip install -r requirements.txt

echo.
echo Running database migrations...
python manage.py migrate

echo.
echo Starting Django server...
echo Open http://127.0.0.1:8000/
echo.
python manage.py runserver 0.0.0.0:8000

endlocal
