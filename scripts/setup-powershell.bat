@echo off
REM PDF to Excel SaaS - Windows PowerShell Setup Helper
REM This script helps set up PowerShell execution policy

echo.
echo ===============================================
echo  PowerShell Execution Policy Setup Helper
echo ===============================================
echo.

REM Check current execution policy
echo Checking current PowerShell execution policy...
for /f "tokens=*" %%a in ('powershell -Command "Get-ExecutionPolicy"') do set CURRENT_POLICY=%%a
echo Current policy: %CURRENT_POLICY%
echo.

if /i "%CURRENT_POLICY%"=="Restricted" (
    echo ❌ PowerShell execution policy is Restricted - scripts cannot run
    echo.
    echo This needs to be changed to allow deployment scripts to work.
    echo.
    echo Recommended solutions:
    echo.
    echo 1. Set RemoteSigned for current user ^(safest^):
    echo    PowerShell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
    echo.
    echo 2. Use bypass for each script ^(temporary^):
    echo    PowerShell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1
    echo.
    echo 3. Set RemoteSigned for all users ^(requires admin^):
    echo    PowerShell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force"
    echo.
    
    set /p choice="Would you like to set RemoteSigned for current user? (y/N): "
    if /i "%choice%"=="y" (
        echo.
        echo Setting execution policy to RemoteSigned for current user...
        powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
        
        if %errorlevel% equ 0 (
            echo ✅ Execution policy changed successfully!
            echo.
            echo Verifying change...
            for /f "tokens=*" %%a in ('powershell -Command "Get-ExecutionPolicy"') do set NEW_POLICY=%%a
            echo New policy: %NEW_POLICY%
            echo.
            if /i "%NEW_POLICY%"=="RemoteSigned" (
                echo ✅ PowerShell is now configured correctly for deployment scripts
            ) else (
                echo ⚠️  Policy may not have changed completely - you can still use bypass method
            )
        ) else (
            echo ❌ Failed to change execution policy
            echo You can still use the bypass method for individual scripts
        )
    ) else (
        echo.
        echo No changes made to execution policy.
        echo You can use bypass method: PowerShell -ExecutionPolicy Bypass -File script.ps1
    )
) else (
    echo ✅ PowerShell execution policy is already set to: %CURRENT_POLICY%
    echo This should allow deployment scripts to run.
)

echo.
echo === Manual Commands Reference ===
echo.
echo To change policy for current user:
echo   PowerShell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
echo.
echo To run scripts with bypass:
echo   PowerShell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1
echo   PowerShell -ExecutionPolicy Bypass -File scripts\setup-github-secrets.ps1
echo.
echo To check current policy:
echo   PowerShell -Command "Get-ExecutionPolicy"
echo.

pause