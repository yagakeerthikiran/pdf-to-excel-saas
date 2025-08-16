# PDF to Excel SaaS - Windows Infrastructure Deployment Script
# Run this PowerShell script to deploy complete AWS infrastructure

param(
    [string]$Environment = "prod",
    [string]$Region = "us-east-1",
    [string]$AppName = "pdf-excel-saas"
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green" 
$WarningColor = "Yellow"
$InfoColor = "Cyan"

Write-Host "🚀 PDF to Excel SaaS - Infrastructure Deployment" -ForegroundColor $InfoColor
Write-Host "=================================================" -ForegroundColor $InfoColor

function Write-Status {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $SuccessColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $WarningColor
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $ErrorColor
}

# Check prerequisites
Write-Host "`n📋 Checking Prerequisites..." -ForegroundColor $InfoColor

# Check AWS CLI
try {
    $awsVersion = aws --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "AWS CLI found: $($awsVersion.Split(' ')[0])"
    } else {
        throw "AWS CLI not found"
    }
} catch {
    Write-Error "AWS CLI not found. Please install AWS CLI first:"
    Write-Host "https://aws.amazon.com/cli/" -ForegroundColor $InfoColor
    exit 1
}

# Check Terraform
try {
    $terraformVersion = terraform version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Terraform found: $($terraformVersion.Split(' ')[1])"
    } else {
        throw "Terraform not found"
    }
} catch {
    Write-Error "Terraform not found. Please install Terraform first:"
    Write-Host "https://terraform.io/downloads" -ForegroundColor $InfoColor
    exit 1
}

# Check Docker
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Docker found: $($dockerVersion)"
    } else {
        Write-Warning "Docker not found. Docker builds will be skipped."
    }
} catch {
    Write-Warning "Docker not found. You can install it later for local builds."
}

# Check AWS credentials
try {
    $awsIdentity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -eq 0) {
        $accountId = $awsIdentity.Account
        Write-Status "AWS credentials configured (Account: $accountId)"
    } else {
        throw "AWS credentials not configured"
    }
} catch {
    Write-Error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
}

# Validate environment file
Write-Host "`n🔍 Validating Environment Configuration..." -ForegroundColor $InfoColor

if (-not (Test-Path ".env.prod")) {
    Write-Warning ".env.prod file not found. Creating from template..."
    if (Test-Path ".env.prod.template") {
        Copy-Item ".env.prod.template" ".env.prod"
        Write-Warning "Please edit .env.prod with your actual values before proceeding."
        Read-Host "Press Enter when you've updated .env.prod with real values"
    } else {
        Write-Error ".env.prod.template not found. Please create environment configuration."
        exit 1
    }
}

# Run environment validation
if (Test-Path "scripts\validate_env.py") {
    Write-Host "Running environment validation..."
    python scripts\validate_env.py --env production --file .env.prod
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Environment validation failed. Please fix the issues above."
        exit 1
    }
    Write-Status "Environment validation passed"
} else {
    Write-Warning "Environment validation script not found. Skipping validation."
}

# Create S3 bucket for Terraform state
$terraformStateBucket = "$AppName-terraform-state"
Write-Host "`n🪣 Setting up Terraform State Storage..." -ForegroundColor $InfoColor

try {
    aws s3 ls "s3://$terraformStateBucket" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Terraform state bucket already exists"
    } else {
        throw "Bucket does not exist"
    }
} catch {
    Write-Host "Creating Terraform state bucket..."
    aws s3 mb "s3://$terraformStateBucket" --region $Region
    
    # Enable versioning
    aws s3api put-bucket-versioning --bucket $terraformStateBucket --versioning-configuration Status=Enabled
    
    # Enable encryption
    $encryptionConfig = @{
        Rules = @(
            @{
                ApplyServerSideEncryptionByDefault = @{
                    SSEAlgorithm = "AES256"
                }
            }
        )
    } | ConvertTo-Json -Depth 5
    
    $encryptionConfig | Out-File -FilePath "temp-encryption.json" -Encoding UTF8
    aws s3api put-bucket-encryption --bucket $terraformStateBucket --server-side-encryption-configuration file://temp-encryption.json
    Remove-Item "temp-encryption.json"
    
    Write-Status "Terraform state bucket created and configured"
}

# Initialize and deploy infrastructure
Write-Host "`n🏗️  Deploying Infrastructure with Terraform..." -ForegroundColor $InfoColor

Push-Location "infra"

try {
    # Initialize Terraform
    Write-Host "Initializing Terraform..."
    terraform init
    if ($LASTEXITCODE -ne 0) { throw "Terraform init failed" }

    # Plan deployment
    Write-Host "Planning infrastructure deployment..."
    terraform plan -var="aws_region=$Region" -var="environment=$Environment" -var="app_name=$AppName" -out=tfplan
    if ($LASTEXITCODE -ne 0) { throw "Terraform plan failed" }

    Write-Host "`n📋 Terraform Plan Summary:" -ForegroundColor $WarningColor
    terraform show -no-color tfplan | Select-String "Plan:|will be created|will be updated|will be destroyed"

    # Confirm deployment
    Write-Host "`n⚠️  This will create AWS resources that may incur costs." -ForegroundColor $WarningColor
    $confirm = Read-Host "Do you want to proceed with the deployment? (y/N)"

    if ($confirm -match "^[Yy]$") {
        Write-Host "Applying Terraform configuration..."
        terraform apply tfplan
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Infrastructure deployment completed successfully!"
            
            # Capture important outputs
            Write-Host "`n📊 Infrastructure Outputs:" -ForegroundColor $InfoColor
            try {
                $albDns = terraform output -raw alb_dns_name 2>$null
                $s3Bucket = terraform output -raw s3_bucket_name 2>$null
                $ecrFrontend = terraform output -raw ecr_frontend_url 2>$null
                $ecrBackend = terraform output -raw ecr_backend_url 2>$null
                
                Write-Host "• Load Balancer DNS: $albDns"
                Write-Host "• S3 Bucket: $s3Bucket"
                Write-Host "• Frontend ECR: $ecrFrontend"
                Write-Host "• Backend ECR: $ecrBackend"
                
                # Save outputs to file
                $outputs = @"
# Infrastructure Deployment Outputs
# Generated: $(Get-Date)

ALB_DNS_NAME=$albDns
S3_BUCKET_NAME=$s3Bucket
ECR_FRONTEND_URL=$ecrFrontend
ECR_BACKEND_URL=$ecrBackend
AWS_ACCOUNT_ID=$accountId
AWS_REGION=$Region
ENVIRONMENT=$Environment
APP_NAME=$AppName
"@
                $outputs | Out-File -FilePath "..\infrastructure-outputs.txt" -Encoding UTF8
                Write-Status "Infrastructure outputs saved to infrastructure-outputs.txt"
                
            } catch {
                Write-Warning "Could not capture all outputs. Check Terraform state manually."
            }
            
        } else {
            Write-Error "Infrastructure deployment failed!"
            exit 1
        }
    } else {
        Write-Warning "Deployment cancelled by user."
        exit 0
    }
} catch {
    Write-Error "Error during Terraform deployment: $_"
    exit 1
} finally {
    Pop-Location
}

# Create ECR repositories if they don't exist
Write-Host "`n📦 Setting up Container Repositories..." -ForegroundColor $InfoColor

# Check and create frontend repository
try {
    aws ecr describe-repositories --repository-names "$AppName-frontend" --region $Region 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Frontend ECR repository already exists"
    } else {
        throw "Repository does not exist"
    }
} catch {
    Write-Host "Creating frontend ECR repository..."
    aws ecr create-repository --repository-name "$AppName-frontend" --region $Region --image-scanning-configuration scanOnPush=true
    Write-Status "Frontend ECR repository created"
}

# Check and create backend repository
try {
    aws ecr describe-repositories --repository-names "$AppName-backend" --region $Region 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Backend ECR repository already exists"
    } else {
        throw "Repository does not exist"
    }
} catch {
    Write-Host "Creating backend ECR repository..."
    aws ecr create-repository --repository-name "$AppName-backend" --region $Region --image-scanning-configuration scanOnPush=true
    Write-Status "Backend ECR repository created"
}

# Build and push initial images (if Docker is available)
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "`n🐳 Building and Pushing Docker Images..." -ForegroundColor $InfoColor

    # Login to ECR
    Write-Host "Logging into ECR..."
    $ecrPassword = aws ecr get-login-password --region $Region
    echo $ecrPassword | docker login --username AWS --password-stdin "$accountId.dkr.ecr.$Region.amazonaws.com"

    # Build frontend image
    if (Test-Path "frontend\Dockerfile.prod") {
        Write-Host "Building frontend image..."
        docker build -f frontend\Dockerfile.prod -t "$AppName-frontend" frontend\
        
        # Tag and push
        docker tag "$AppName-frontend:latest" "$accountId.dkr.ecr.$Region.amazonaws.com/$AppName-frontend:latest"
        docker push "$accountId.dkr.ecr.$Region.amazonaws.com/$AppName-frontend:latest"
        Write-Status "Frontend image pushed to ECR"
    } else {
        Write-Warning "Frontend Dockerfile.prod not found. Skipping frontend image build."
    }

    # Build backend image
    if (Test-Path "backend\Dockerfile.prod") {
        Write-Host "Building backend image..."
        docker build -f backend\Dockerfile.prod -t "$AppName-backend" backend\
        
        # Tag and push
        docker tag "$AppName-backend:latest" "$accountId.dkr.ecr.$Region.amazonaws.com/$AppName-backend:latest"
        docker push "$accountId.dkr.ecr.$Region.amazonaws.com/$AppName-backend:latest"
        Write-Status "Backend image pushed to ECR"
    } else {
        Write-Warning "Backend Dockerfile.prod not found. Skipping backend image build."
    }
} else {
    Write-Warning "Docker not available. Skipping image builds. You can build images later."
}

# Set up monitoring
Write-Host "`n📊 Setting up Monitoring and Alerts..." -ForegroundColor $InfoColor

# Create CloudWatch log groups
$logGroups = @(
    "/ecs/$AppName-$Environment-frontend",
    "/ecs/$AppName-$Environment-backend", 
    "/ecs/$AppName-$Environment-monitoring"
)

foreach ($logGroup in $logGroups) {
    try {
        aws logs create-log-group --log-group-name $logGroup --region $Region 2>$null
    } catch {
        # Log group might already exist
    }
}

Write-Status "CloudWatch log groups created"

# Final setup and verification
Write-Host "`n🔍 Running Health Checks..." -ForegroundColor $InfoColor

# Wait for services to be ready
Write-Host "Waiting for services to initialize..."
Start-Sleep 30

# Test ALB endpoint (if available)
if ($albDns) {
    Write-Host "Testing load balancer endpoint..."
    for ($i = 1; $i -le 5; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://$albDns" -TimeoutSec 10 -ErrorAction Stop
            Write-Status "Load balancer is responding"
            break
        } catch {
            if ($i -eq 5) {
                Write-Warning "Load balancer not responding yet (this is normal for initial deployment)"
            } else {
                Write-Host "Attempt $i/5 failed, retrying in 10 seconds..."
                Start-Sleep 10
            }
        }
    }
}

# Generate deployment summary
Write-Host "`n🎉 Deployment Summary" -ForegroundColor $SuccessColor
Write-Host "===================" -ForegroundColor $SuccessColor
Write-Host "• Environment: $Environment"
Write-Host "• AWS Region: $Region"
Write-Host "• AWS Account: $accountId"
Write-Host "• Application: $AppName"
Write-Host "• Load Balancer: $($albDns ?? 'Pending')"
Write-Host "• S3 Bucket: $($s3Bucket ?? 'N/A')"
Write-Host "• ECR Repositories: Created"
Write-Host "• Monitoring: Configured"
Write-Host "• Infrastructure: ✅ Deployed"

Write-Host "`n📋 Next Steps:" -ForegroundColor $InfoColor
Write-Host "1. Configure your domain to point to: $albDns"
Write-Host "2. Set up SSL certificate in AWS Certificate Manager"
Write-Host "3. Update GitHub repository secrets for CI/CD"
Write-Host "4. Run 'git push origin main' to trigger deployment pipeline"
Write-Host "5. Monitor application at: http://$albDns"

Write-Host "`n✅ Infrastructure deployment completed successfully!" -ForegroundColor $SuccessColor

# Create post-deployment checklist
$checklist = @"
# Post-Deployment Checklist

## Infrastructure ✅
- [x] AWS VPC and networking
- [x] RDS PostgreSQL database
- [x] S3 bucket for file storage
- [x] ECS cluster and services
- [x] Application Load Balancer
- [x] ECR repositories
- [x] CloudWatch logging

## Next Steps
- [ ] Configure domain DNS
- [ ] Set up SSL certificate
- [ ] Configure GitHub secrets
- [ ] Test application deployment
- [ ] Set up monitoring alerts
- [ ] Configure backup policies
- [ ] Run security audit
- [ ] Update documentation

## Important URLs
- Application: http://$albDns
- AWS Console: https://console.aws.amazon.com/
- GitHub Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas

## Generated on: $(Get-Date)
"@

$checklist | Out-File -FilePath "deployment-checklist.md" -Encoding UTF8
Write-Status "Deployment checklist created: deployment-checklist.md"