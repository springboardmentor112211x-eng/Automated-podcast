@echo off
REM Start the Django development server
REM This script starts the server from the correct directory

echo.
echo ========================================
echo Audio Pipeline Server Startup
echo ========================================
echo.

cd /d "%~dp0backend"

echo Starting Django development server...
echo Server will be available at: http://127.0.0.1:8000/
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver --noreload

pause
