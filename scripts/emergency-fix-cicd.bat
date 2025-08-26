@echo off
REM Emergency CI/CD Fix for Windows
REM Fixes ECR 403 Forbidden errors by creating repositories

echo ========================================
echo 🚨 EMERGENCY CI/CD FIX - Windows Version
echo ========================================
echo.

echo 🔍 Checking AWS CLI...
aws --version >nul 2>&1
if errorlevel 1 (
    echo ❌ AWS CLI not found. Please install it first:
    echo    https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
    pause
    exit /b 1
)
echo ✅ AWS CLI found

echo.
echo 🔍 Testing AWS credentials...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ❌ AWS credentials not configured
    echo.
    echo Please run one of these:
    echo 1. aws configure
    echo 2. Or set environment variables:
    echo    set AWS_ACCESS_KEY_ID=your_key
    echo    set AWS_SECRET_ACCESS_KEY=your_secret  
    echo    set AWS_DEFAULT_REGION=ap-southeast-2
    echo.
    pause
    exit /b 1
)
echo ✅ AWS credentials configured

echo.
echo 🏗️ Creating ECR repositories...

echo 📦 Creating pdf-excel-saas-frontend...
aws ecr create-repository --repository-name pdf-excel-saas-frontend --region ap-southeast-2 >nul 2>&1
if errorlevel 1 (
    echo ℹ️ Repository may already exist
) else (
    echo ✅ Created pdf-excel-saas-frontend
)

echo 📦 Creating pdf-excel-saas-backend...
aws ecr create-repository --repository-name pdf-excel-saas-backend --region ap-southeast-2 >nul 2>&1
if errorlevel 1 (
    echo ℹ️ Repository may already exist
) else (
    echo ✅ Created pdf-excel-saas-backend
)

echo.
echo 🧪 Testing ECR authentication...
aws ecr get-authorization-token --region ap-southeast-2 >nul 2>&1
if errorlevel 1 (
    echo ❌ ECR authentication failed
    pause
    exit /b 1
)
echo ✅ ECR authentication successful

echo.
echo 🐳 Testing Docker ECR login...
for /f "tokens=*" %%i in ('aws ecr get-login-password --region ap-southeast-2') do (
    echo %%i | docker login --username AWS --password-stdin 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com >nul 2>&1
)
if errorlevel 1 (
    echo ⚠️ Docker login failed - Docker may not be running
    echo 💡 This is OK - GitHub Actions will handle Docker
) else (
    echo ✅ Docker ECR login successful
)

echo.
echo ========================================
echo 🎯 NEXT STEPS TO FIX CI/CD
echo ========================================
echo.

echo 1. 🔐 SET GITHUB SECRETS:
echo    • Go to: https://github.com/yagakeerthikiran/pdf-to-excel-saas/settings/secrets/actions
echo    • Click 'New repository secret'
echo    • Add: AWS_ACCESS_KEY_ID
echo    • Add: AWS_SECRET_ACCESS_KEY
echo    • Use the SAME credentials that worked in this script
echo.

echo 2. 🚀 TRIGGER CI/CD:
echo    git add .
echo    git commit -m "fix: ECR repositories created, ready for CI/CD"
echo    git push origin feat/infrastructure-clean
echo.

echo 3. 🔍 MONITOR DEPLOYMENT:
echo    • Go to: https://github.com/yagakeerthikiran/pdf-to-excel-saas/actions
echo    • Watch the 'Build and Deploy to AWS ECS' workflow
echo    • Should now succeed instead of ECR 403 errors
echo.

echo 4. ✅ VALIDATE SUCCESS:
echo    • Check if Docker images appear in ECR console
echo    • Verify ECS services are updated  
echo    • Test application at ALB URL
echo.

echo 🎉 ECR SETUP COMPLETE!
echo    ECR repositories created and configured
echo    Ready for GitHub Actions CI/CD
echo    Next: Set GitHub secrets and trigger deployment
echo.

pause
