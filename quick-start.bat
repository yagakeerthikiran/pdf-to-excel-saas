@echo off
REM Quick navigation script - run this from anywhere
echo.
echo =====================================
echo  PDF to Excel SaaS - Quick Start
echo =====================================
echo.

echo Navigating to project directory...
cd /d "C:\AI\GIT_Repos\pdf-to-excel-saas"

if %errorlevel% neq 0 (
    echo ERROR: Could not navigate to C:\AI\GIT_Repos\pdf-to-excel-saas
    echo Please check if the directory exists.
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

if exist "scripts\deploy-windows.bat" (
    echo ✅ Found deployment script
    echo.
    echo Starting deployment interface...
    call scripts\deploy-windows.bat
) else (
    echo ❌ Deployment script not found
    echo Please ensure you have the latest code:
    echo   git pull origin feat/initial-app-foundation
    pause
)

REM Keep the window open if there were any errors
if %errorlevel% neq 0 pause