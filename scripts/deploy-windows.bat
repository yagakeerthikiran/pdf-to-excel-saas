@echo off
REM PDF to Excel SaaS - Windows Quick Deployment
REM This batch file works from any directory and finds the project root

echo.
echo ========================================
echo  PDF to Excel SaaS - Quick Deployment
echo ========================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Change to project root directory
pushd "%PROJECT_ROOT%"

echo Current directory: %CD%
echo Script directory: %SCRIPT_DIR%
echo Project root: %PROJECT_ROOT%
echo.

REM Check if we're in the right directory by looking for key files
if not exist "README.md" (
    echo ERROR: Cannot find README.md - not in project root directory
    echo Please ensure the script is in the correct location
    popd
    pause
    exit /b 1
)

if not exist "scripts\deploy-infrastructure.ps1" (
    echo ERROR: Cannot find scripts\deploy-infrastructure.ps1
    echo Please ensure all files are present in the repository
    popd
    pause
    exit /b 1
)

echo ✅ Found project files - ready to proceed
echo.

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell is available'" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is required but not found.
    echo Please install PowerShell or use Windows 10/11.
    popd
    pause
    exit /b 1
)

:menu
echo Please choose an option:
echo.
echo 1. Validate Environment Configuration
echo 2. Deploy AWS Infrastructure  
echo 3. Setup GitHub Secrets
echo 4. Deploy Complete Application
echo 5. Check Prerequisites
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto validate_env
if "%choice%"=="2" goto deploy_infra
if "%choice%"=="3" goto setup_secrets
if "%choice%"=="4" goto deploy_app
if "%choice%"=="5" goto check_prereq
if "%choice%"=="6" goto exit
echo Invalid choice. Please try again.
goto menu

:validate_env
echo.
echo ===========================================
echo  Validating Environment Configuration
echo ===========================================
echo.
if not exist .env.prod (
    echo WARNING: .env.prod file not found.
    if exist .env.prod.template (
        echo Creating .env.prod from template...
        copy .env.prod.template .env.prod
        echo.
        echo Please edit .env.prod with your actual values and run this again.
        echo Opening .env.prod in notepad...
        start notepad .env.prod
        pause
        goto menu
    ) else (
        echo ERROR: .env.prod.template not found.
        pause
        goto menu
    )
)

if exist scripts\validate_env.py (
    python scripts\validate_env.py --env production --file .env.prod
    if %errorlevel% neq 0 (
        echo.
        echo Validation failed. Please fix the issues above.
        pause
        goto menu
    )
    echo.
    echo Environment validation passed!
) else (
    echo ERROR: Validation script not found at scripts\validate_env.py
)
pause
goto menu

:deploy_infra
echo.
echo ===========================================
echo  Deploying AWS Infrastructure
echo ===========================================
echo.
echo This will create AWS resources that may incur costs.
set /p confirm="Are you sure you want to continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Deployment cancelled.
    pause
    goto menu
)

if exist scripts\deploy-infrastructure.ps1 (
    powershell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1
    if %errorlevel% neq 0 (
        echo.
        echo Infrastructure deployment failed.
        pause
        goto menu
    )
    echo.
    echo Infrastructure deployment completed!
) else (
    echo ERROR: PowerShell script not found at scripts\deploy-infrastructure.ps1
)
pause
goto menu

:setup_secrets
echo.
echo ===========================================
echo  Setting up GitHub Secrets
echo ===========================================
echo.
echo This will configure GitHub repository secrets for CI/CD.
echo You need to be authenticated with GitHub CLI (gh auth login).
echo.
set /p confirm="Continue with GitHub secrets setup? (y/N): "
if /i not "%confirm%"=="y" (
    echo Setup cancelled.
    pause
    goto menu
)

if exist scripts\setup-github-secrets.ps1 (
    powershell -ExecutionPolicy Bypass -File scripts\setup-github-secrets.ps1
    if %errorlevel% neq 0 (
        echo.
        echo GitHub secrets setup failed.
        pause
        goto menu
    )
    echo.
    echo GitHub secrets setup completed!
) else (
    echo ERROR: PowerShell script not found at scripts\setup-github-secrets.ps1
)
pause
goto menu

:deploy_app
echo.
echo ===========================================
echo  Deploying Complete Application
echo ===========================================
echo.
echo This will:
echo 1. Validate environment
echo 2. Deploy infrastructure
echo 3. Setup GitHub secrets
echo 4. Push to main branch (triggers CI/CD)
echo.
set /p confirm="Continue with complete deployment? (y/N): "
if /i not "%confirm%"=="y" (
    echo Deployment cancelled.
    pause
    goto menu
)

REM Validate environment
echo Step 1/4: Validating environment...
if exist scripts\validate_env.py (
    python scripts\validate_env.py --env production --file .env.prod
    if %errorlevel% neq 0 (
        echo Environment validation failed.
        pause
        goto menu
    )
) else (
    echo ERROR: Validation script not found
    pause
    goto menu
)

REM Deploy infrastructure
echo Step 2/4: Deploying infrastructure...
if exist scripts\deploy-infrastructure.ps1 (
    powershell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1
    if %errorlevel% neq 0 (
        echo Infrastructure deployment failed.
        pause
        goto menu
    )
) else (
    echo ERROR: Infrastructure script not found
    pause
    goto menu
)

REM Setup GitHub secrets
echo Step 3/4: Setting up GitHub secrets...
if exist scripts\setup-github-secrets.ps1 (
    powershell -ExecutionPolicy Bypass -File scripts\setup-github-secrets.ps1
    if %errorlevel% neq 0 (
        echo GitHub secrets setup failed.
        pause
        goto menu
    )
) else (
    echo ERROR: GitHub secrets script not found
    pause
    goto menu
)

REM Deploy application
echo Step 4/4: Deploying application...
echo Adding changes to git...
git add .
git commit -m "Production deployment configuration"
echo Pushing to main branch to trigger deployment...
git push origin feat/initial-app-foundation:main

echo.
echo ================================================
echo  Complete deployment initiated successfully!
echo ================================================
echo.
echo Your application is now deploying via GitHub Actions.
echo.
echo Monitor the deployment at:
echo https://github.com/yagakeerthikiran/pdf-to-excel-saas/actions
echo.
pause
goto menu

:check_prereq
echo.
echo ===========================================
echo  Checking Prerequisites
echo ===========================================
echo.

REM Check current directory and files
echo Current directory: %CD%
echo.

echo === Project Files ===
if exist README.md (
    echo [OK] README.md found - in project root
) else (
    echo [ERROR] README.md not found - not in project root
)

if exist scripts\deploy-infrastructure.ps1 (
    echo [OK] deploy-infrastructure.ps1 found
) else (
    echo [MISSING] deploy-infrastructure.ps1
)

if exist scripts\setup-github-secrets.ps1 (
    echo [OK] setup-github-secrets.ps1 found
) else (
    echo [MISSING] setup-github-secrets.ps1
)

if exist scripts\validate_env.py (
    echo [OK] validate_env.py found
) else (
    echo [MISSING] validate_env.py
)

if exist .env.prod.template (
    echo [OK] .env.prod.template found
) else (
    echo [MISSING] .env.prod.template
)

if exist .env.prod (
    echo [OK] .env.prod found
) else (
    echo [INFO] .env.prod not found (will be created from template)
)

echo.
echo === Required Software ===

REM Check Git
git --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Git is installed
) else (
    echo [MISSING] Git - Download from https://git-scm.com/
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python is installed
) else (
    echo [MISSING] Python - Download from https://python.org/
)

REM Check AWS CLI
aws --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] AWS CLI is installed
) else (
    echo [MISSING] AWS CLI - Download from https://aws.amazon.com/cli/
)

REM Check Terraform
terraform version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Terraform is installed
) else (
    echo [MISSING] Terraform - Download from https://terraform.io/downloads
)

REM Check GitHub CLI
gh --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] GitHub CLI is installed
) else (
    echo [MISSING] GitHub CLI - Download from https://cli.github.com/
)

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker is installed
) else (
    echo [OPTIONAL] Docker - Download from https://docker.com/
)

echo.
echo === Authentication Status ===
aws sts get-caller-identity >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] AWS CLI is configured
) else (
    echo [MISSING] AWS CLI not configured - Run 'aws configure'
)

gh auth status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] GitHub CLI is authenticated
) else (
    echo [MISSING] GitHub CLI not authenticated - Run 'gh auth login'
)

echo.
echo === PowerShell Status ===
powershell -Command "Write-Host 'PowerShell Version:' $PSVersionTable.PSVersion.ToString()" 2>nul
powershell -Command "Write-Host 'Execution Policy:' (Get-ExecutionPolicy)" 2>nul

echo.
pause
goto menu

:exit
popd
echo.
echo Thank you for using PDF to Excel SaaS deployment!
echo.
echo Useful links:
echo - AWS Console: https://console.aws.amazon.com/
echo - GitHub Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas
echo - Documentation: PRODUCTION-DEPLOYMENT.md
echo.
pause
exit /b 0