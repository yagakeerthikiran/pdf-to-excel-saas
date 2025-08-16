@echo off
REM PDF to Excel SaaS - Windows Quick Deployment
REM This batch file provides a simple interface for Windows users

echo.
echo ========================================
echo  PDF to Excel SaaS - Quick Deployment
echo ========================================
echo.

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell is available'" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is required but not found.
    echo Please install PowerShell or use Windows 10/11.
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
        notepad .env.prod
        pause
        goto menu
    ) else (
        echo ERROR: .env.prod.template not found.
        pause
        goto menu
    )
)

python scripts/validate_env.py --env production --file .env.prod
if %errorlevel% neq 0 (
    echo.
    echo Validation failed. Please fix the issues above.
    pause
    goto menu
)
echo.
echo Environment validation passed!
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

powershell -ExecutionPolicy Bypass -File scripts/deploy-infrastructure.ps1
if %errorlevel% neq 0 (
    echo.
    echo Infrastructure deployment failed.
    pause
    goto menu
)
echo.
echo Infrastructure deployment completed!
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

powershell -ExecutionPolicy Bypass -File scripts/setup-github-secrets.ps1
if %errorlevel% neq 0 (
    echo.
    echo GitHub secrets setup failed.
    pause
    goto menu
)
echo.
echo GitHub secrets setup completed!
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
python scripts/validate_env.py --env production --file .env.prod
if %errorlevel% neq 0 (
    echo Environment validation failed.
    pause
    goto menu
)

REM Deploy infrastructure
echo Step 2/4: Deploying infrastructure...
powershell -ExecutionPolicy Bypass -File scripts/deploy-infrastructure.ps1
if %errorlevel% neq 0 (
    echo Infrastructure deployment failed.
    pause
    goto menu
)

REM Setup GitHub secrets
echo Step 3/4: Setting up GitHub secrets...
powershell -ExecutionPolicy Bypass -File scripts/setup-github-secrets.ps1
if %errorlevel% neq 0 (
    echo GitHub secrets setup failed.
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
echo AWS CLI Authentication Status:
aws sts get-caller-identity >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] AWS CLI is configured
) else (
    echo [MISSING] AWS CLI not configured - Run 'aws configure'
)

echo.
echo GitHub CLI Authentication Status:
gh auth status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] GitHub CLI is authenticated
) else (
    echo [MISSING] GitHub CLI not authenticated - Run 'gh auth login'
)

echo.
pause
goto menu

:exit
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