@echo off
REM Quick fix for PowerShell script syntax error

echo.
echo =====================================
echo  PowerShell Script Quick Fix
echo =====================================
echo.

echo Checking if you have the latest version...

REM Check if the problematic line exists
findstr /n "} else {" scripts\deploy-infrastructure.ps1 > nul
if %errorlevel% equ 0 (
    echo Found syntax error in PowerShell script.
    echo.
    echo Option 1: Pull latest changes from repository
    echo   git pull origin feat/initial-app-foundation
    echo.
    echo Option 2: Download fixed version manually
    echo   Go to: https://github.com/yagakeerthikiran/pdf-to-excel-saas/blob/feat/initial-app-foundation/scripts/deploy-infrastructure.ps1
    echo   Copy the content and replace your local file
    echo.
    echo Option 3: Use manual Terraform commands
    echo   cd infra
    echo   terraform init
    echo   terraform plan
    echo   terraform apply
    echo.
    
    set /p choice="Try to pull latest changes automatically? (y/N): "
    if /i "%choice%"=="y" (
        echo Pulling latest changes...
        git pull origin feat/initial-app-foundation
        if %errorlevel% equ 0 (
            echo ✅ Successfully pulled latest changes
            echo Now try running: scripts\deploy-windows.bat
        ) else (
            echo ❌ Git pull failed. Try manual options above.
        )
    )
) else (
    echo ✅ PowerShell script appears to be the latest version
)

echo.
pause