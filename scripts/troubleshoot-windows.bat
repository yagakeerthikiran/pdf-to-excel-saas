@echo off
REM PDF to Excel SaaS - Windows Troubleshooting Script
REM This script helps diagnose and fix common Windows deployment issues

echo.
echo ===============================================
echo  PDF to Excel SaaS - Windows Troubleshooting
echo ===============================================
echo.

echo Current Directory: %CD%
echo.

echo === Checking File Structure ===
echo.

REM Check if we're in the right directory
if exist "README.md" (
    echo [OK] Found README.md - appears to be in project root
) else (
    echo [ERROR] README.md not found - you may not be in the project root directory
    echo Please navigate to the pdf-to-excel-saas directory and try again
    pause
    exit /b 1
)

if exist "scripts" (
    echo [OK] scripts directory exists
) else (
    echo [ERROR] scripts directory not found
    echo Please ensure you're in the correct project directory
    pause
    exit /b 1
)

REM Check for all required script files
echo.
echo === Checking Script Files ===
echo.

if exist "scripts\deploy-windows.bat" (
    echo [OK] deploy-windows.bat found
) else (
    echo [MISSING] deploy-windows.bat
)

if exist "scripts\deploy-infrastructure.ps1" (
    echo [OK] deploy-infrastructure.ps1 found
) else (
    echo [MISSING] deploy-infrastructure.ps1
)

if exist "scripts\setup-github-secrets.ps1" (
    echo [OK] setup-github-secrets.ps1 found
) else (
    echo [MISSING] setup-github-secrets.ps1
)

if exist "scripts\validate_env.py" (
    echo [OK] validate_env.py found
) else (
    echo [MISSING] validate_env.py
)

REM Check environment files
echo.
echo === Checking Environment Files ===
echo.

if exist ".env.prod.template" (
    echo [OK] .env.prod.template found
) else (
    echo [MISSING] .env.prod.template
)

if exist ".env.prod" (
    echo [OK] .env.prod found
) else (
    echo [INFO] .env.prod not found (will be created from template)
)

REM Check Git status
echo.
echo === Checking Git Status ===
echo.

git status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Git repository detected
    echo Current branch:
    git branch --show-current
    echo.
    echo Latest commit:
    git log --oneline -1
) else (
    echo [ERROR] Not a Git repository or Git not installed
)

REM Check PowerShell execution policy
echo.
echo === Checking PowerShell Configuration ===
echo.

powershell -Command "Write-Host 'PowerShell Version: ' $PSVersionTable.PSVersion.ToString()" 2>nul
powershell -Command "Write-Host 'Execution Policy: ' (Get-ExecutionPolicy)" 2>nul

echo.
echo === Testing PowerShell Script Access ===
echo.

if exist "scripts\deploy-infrastructure.ps1" (
    powershell -Command "Test-Path 'scripts\deploy-infrastructure.ps1'" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] PowerShell can access deploy-infrastructure.ps1
    ) else (
        echo [ERROR] PowerShell cannot access deploy-infrastructure.ps1
    )
) else (
    echo [SKIP] deploy-infrastructure.ps1 not found
)

REM Check for common Windows issues
echo.
echo === Checking for Common Issues ===
echo.

REM Check if files are blocked
powershell -Command "Get-ChildItem scripts\*.ps1 | Get-Item -Stream Zone.Identifier -ErrorAction SilentlyContinue" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Some PowerShell scripts may be blocked by Windows
    echo [FIX] Run this command to unblock them:
    echo powershell -Command "Get-ChildItem scripts\*.ps1 | Unblock-File"
) else (
    echo [OK] PowerShell scripts are not blocked
)

REM Check line endings
echo.
echo === Suggested Fixes for Common Issues ===
echo.

echo 1. If PowerShell execution policy errors occur:
echo    powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
echo.

echo 2. If scripts are blocked by Windows:
echo    powershell -Command "Get-ChildItem scripts\*.ps1 | Unblock-File"
echo.

echo 3. If Git line ending issues occur:
echo    git config --global core.autocrlf true
echo.

echo 4. To run scripts with bypass:
echo    PowerShell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1
echo.

echo 5. If you need to pull latest changes:
echo    git pull origin feat/initial-app-foundation
echo.

echo === Quick Fix Commands ===
echo.
set /p fix="Do you want to apply common fixes automatically? (y/N): "
if /i "%fix%"=="y" (
    echo.
    echo Applying fixes...
    
    echo Unblocking PowerShell scripts...
    powershell -Command "Get-ChildItem scripts\*.ps1 -ErrorAction SilentlyContinue | Unblock-File" 2>nul
    
    echo Setting PowerShell execution policy for current user...
    powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force" 2>nul
    
    echo Configuring Git for Windows...
    git config --global core.autocrlf true 2>nul
    
    echo.
    echo Fixes applied! Try running the deployment script again.
)

echo.
echo === Manual Deployment Commands ===
echo.
echo If the batch file still doesn't work, try these manual commands:
echo.
echo 1. Validate environment:
echo    python scripts\validate_env.py --env production --file .env.prod
echo.
echo 2. Deploy infrastructure:
echo    PowerShell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1
echo.
echo 3. Setup GitHub secrets:
echo    PowerShell -ExecutionPolicy Bypass -File scripts\setup-github-secrets.ps1
echo.

echo === Troubleshooting Complete ===
echo.
echo If you're still having issues:
echo 1. Check that you're in the project root directory
echo 2. Ensure you have the latest code: git pull origin feat/initial-app-foundation
echo 3. Check prerequisites: all required tools are installed
echo 4. Try the manual commands listed above
echo.

pause