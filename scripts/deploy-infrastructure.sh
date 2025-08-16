#!/bin/bash
# Production Infrastructure Deployment Script
# Run this script to deploy complete AWS infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-prod}
APP_NAME=${APP_NAME:-pdf-excel-saas}
TERRAFORM_STATE_BUCKET="${APP_NAME}-terraform-state"

echo -e "${BLUE}🚀 PDF to Excel SaaS - Infrastructure Deployment${NC}"
echo -e "${BLUE}=================================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
echo -e "\n${BLUE}📋 Checking Prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi
print_status "AWS CLI found"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    print_error "Terraform not found. Please install Terraform first."
    exit 1
fi
print_status "Terraform found"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "AWS credentials configured (Account: $AWS_ACCOUNT_ID)"

# Validate environment file
echo -e "\n${BLUE}🔍 Validating Environment Configuration...${NC}"

if [ ! -f ".env.prod" ]; then
    print_warning ".env.prod file not found. Creating from template..."
    if [ -f ".env.prod.template" ]; then
        cp .env.prod.template .env.prod
        print_warning "Please edit .env.prod with your actual values before proceeding."
        read -p "Press Enter when you've updated .env.prod with real values..."
    else
        print_error ".env.prod.template not found. Please create environment configuration."
        exit 1
    fi
fi

# Run environment validation
if [ -f "scripts/validate_env.py" ]; then
    echo "Running environment validation..."
    python3 scripts/validate_env.py --env production --file .env.prod
    if [ $? -ne 0 ]; then
        print_error "Environment validation failed. Please fix the issues above."
        exit 1
    fi
    print_status "Environment validation passed"
else
    print_warning "Environment validation script not found. Skipping validation."
fi

# Create S3 bucket for Terraform state
echo -e "\n${BLUE}🪣 Setting up Terraform State Storage...${NC}"

if aws s3 ls "s3://$TERRAFORM_STATE_BUCKET" 2>/dev/null; then
    print_status "Terraform state bucket already exists"
else
    echo "Creating Terraform state bucket..."
    aws s3 mb "s3://$TERRAFORM_STATE_BUCKET" --region $AWS_REGION
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$TERRAFORM_STATE_BUCKET" \
        --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "$TERRAFORM_STATE_BUCKET" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    
    print_status "Terraform state bucket created and configured"
fi

# Initialize and deploy infrastructure
echo -e "\n${BLUE}🏗️  Deploying Infrastructure with Terraform...${NC}"

cd infra

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan deployment
echo "Planning infrastructure deployment..."
terraform plan \
    -var="aws_region=$AWS_REGION" \
    -var="environment=$ENVIRONMENT" \
    -var="app_name=$APP_NAME" \
    -out=tfplan

echo -e "\n${YELLOW}📋 Terraform Plan Summary:${NC}"
terraform show -no-color tfplan | grep -E "Plan:|will be created|will be updated|will be destroyed" || true

# Confirm deployment
echo -e "\n${YELLOW}⚠️  This will create AWS resources that may incur costs.${NC}"
read -p "Do you want to proceed with the deployment? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    echo "Applying Terraform configuration..."
    terraform apply tfplan
    
    if [ $? -eq 0 ]; then
        print_status "Infrastructure deployment completed successfully!"
        
        # Capture important outputs
        echo -e "\n${BLUE}📊 Infrastructure Outputs:${NC}"
        ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "N/A")
        S3_BUCKET=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "N/A")
        ECR_FRONTEND=$(terraform output -raw ecr_frontend_url 2>/dev/null || echo "N/A")
        ECR_BACKEND=$(terraform output -raw ecr_backend_url 2>/dev/null || echo "N/A")
        
        echo "• Load Balancer DNS: $ALB_DNS"
        echo "• S3 Bucket: $S3_BUCKET"
        echo "• Frontend ECR: $ECR_FRONTEND"
        echo "• Backend ECR: $ECR_BACKEND"
        
        # Save outputs to file
        cat > ../infrastructure-outputs.txt << EOF
# Infrastructure Deployment Outputs
# Generated: $(date)

ALB_DNS_NAME=$ALB_DNS
S3_BUCKET_NAME=$S3_BUCKET
ECR_FRONTEND_URL=$ECR_FRONTEND
ECR_BACKEND_URL=$ECR_BACKEND
AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
AWS_REGION=$AWS_REGION
ENVIRONMENT=$ENVIRONMENT
APP_NAME=$APP_NAME
EOF
        
        print_status "Infrastructure outputs saved to infrastructure-outputs.txt"
        
    else
        print_error "Infrastructure deployment failed!"
        exit 1
    fi
else
    print_warning "Deployment cancelled by user."
    exit 0
fi

cd ..

# Create ECR repositories if they don't exist
echo -e "\n${BLUE}📦 Setting up Container Repositories...${NC}"

# Check and create frontend repository
if aws ecr describe-repositories --repository-names "${APP_NAME}-frontend" --region $AWS_REGION >/dev/null 2>&1; then
    print_status "Frontend ECR repository already exists"
else
    echo "Creating frontend ECR repository..."
    aws ecr create-repository \
        --repository-name "${APP_NAME}-frontend" \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
    print_status "Frontend ECR repository created"
fi

# Check and create backend repository
if aws ecr describe-repositories --repository-names "${APP_NAME}-backend" --region $AWS_REGION >/dev/null 2>&1; then
    print_status "Backend ECR repository already exists"
else
    echo "Creating backend ECR repository..."
    aws ecr create-repository \
        --repository-name "${APP_NAME}-backend" \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
    print_status "Backend ECR repository created"
fi

# Build and push initial images
echo -e "\n${BLUE}🐳 Building and Pushing Docker Images...${NC}"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build frontend image
if [ -f "frontend/Dockerfile.prod" ]; then
    echo "Building frontend image..."
    docker build -f frontend/Dockerfile.prod -t "${APP_NAME}-frontend" frontend/
    
    # Tag and push
    docker tag "${APP_NAME}-frontend:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${APP_NAME}-frontend:latest"
    docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${APP_NAME}-frontend:latest"
    print_status "Frontend image pushed to ECR"
else
    print_warning "Frontend Dockerfile.prod not found. Skipping frontend image build."
fi

# Build backend image
if [ -f "backend/Dockerfile.prod" ]; then
    echo "Building backend image..."
    docker build -f backend/Dockerfile.prod -t "${APP_NAME}-backend" backend/
    
    # Tag and push
    docker tag "${APP_NAME}-backend:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${APP_NAME}-backend:latest"
    docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${APP_NAME}-backend:latest"
    print_status "Backend image pushed to ECR"
else
    print_warning "Backend Dockerfile.prod not found. Skipping backend image build."
fi

# Set up monitoring
echo -e "\n${BLUE}📊 Setting up Monitoring and Alerts...${NC}"

# Create CloudWatch log groups
aws logs create-log-group --log-group-name "/ecs/${APP_NAME}-${ENVIRONMENT}-frontend" --region $AWS_REGION 2>/dev/null || true
aws logs create-log-group --log-group-name "/ecs/${APP_NAME}-${ENVIRONMENT}-backend" --region $AWS_REGION 2>/dev/null || true
aws logs create-log-group --log-group-name "/ecs/${APP_NAME}-${ENVIRONMENT}-monitoring" --region $AWS_REGION 2>/dev/null || true

print_status "CloudWatch log groups created"

# Deploy monitoring agent
if [ -f "monitoring/intelligent_agent.py" ]; then
    echo "Deploying monitoring agent..."
    
    # Create monitoring task definition
    cat > monitoring-task-def.json << EOF
{
  "family": "${APP_NAME}-${ENVIRONMENT}-monitoring",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${APP_NAME}-${ENVIRONMENT}-ecs-task-execution-role",
  "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${APP_NAME}-${ENVIRONMENT}-ecs-task-role",
  "containerDefinitions": [
    {
      "name": "monitoring-agent",
      "image": "python:3.11-slim",
      "command": [
        "sh", "-c",
        "pip install requests boto3 && python /app/monitoring/intelligent_agent.py"
      ],
      "environment": [
        {"name": "AUTO_FIX_ENABLED", "value": "true"},
        {"name": "MONITORING_INTERVAL", "value": "60"},
        {"name": "ERROR_THRESHOLD", "value": "10"},
        {"name": "AWS_REGION", "value": "${AWS_REGION}"},
        {"name": "ECS_CLUSTER", "value": "${APP_NAME}-${ENVIRONMENT}"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${APP_NAME}-${ENVIRONMENT}-monitoring",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

    # Register task definition
    aws ecs register-task-definition \
        --cli-input-json file://monitoring-task-def.json \
        --region $AWS_REGION

    print_status "Monitoring agent configured"
    rm monitoring-task-def.json
else
    print_warning "Monitoring agent not found. Skipping monitoring setup."
fi

# Final setup and verification
echo -e "\n${BLUE}🔍 Running Health Checks...${NC}"

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 30

# Test ALB endpoint
if [ "$ALB_DNS" != "N/A" ]; then
    echo "Testing load balancer endpoint..."
    for i in {1..5}; do
        if curl -f -s "http://$ALB_DNS" >/dev/null 2>&1; then
            print_status "Load balancer is responding"
            break
        elif [ $i -eq 5 ]; then
            print_warning "Load balancer not responding yet (this is normal for initial deployment)"
        else
            echo "Attempt $i/5 failed, retrying in 10 seconds..."
            sleep 10
        fi
    done
fi

# Generate deployment summary
echo -e "\n${GREEN}🎉 Deployment Summary${NC}"
echo -e "${GREEN}===================${NC}"
echo "• Environment: $ENVIRONMENT"
echo "• AWS Region: $AWS_REGION"
echo "• AWS Account: $AWS_ACCOUNT_ID"
echo "• Application: $APP_NAME"
echo "• Load Balancer: ${ALB_DNS:-Pending}"
echo "• S3 Bucket: ${S3_BUCKET:-N/A}"
echo "• ECR Repositories: Created"
echo "• Monitoring: Configured"
echo "• Infrastructure: ✅ Deployed"

echo -e "\n${BLUE}📋 Next Steps:${NC}"
echo "1. Configure your domain to point to: $ALB_DNS"
echo "2. Set up SSL certificate in AWS Certificate Manager"
echo "3. Update GitHub repository secrets for CI/CD"
echo "4. Run 'git push origin main' to trigger deployment pipeline"
echo "5. Monitor application at: http://$ALB_DNS"

echo -e "\n${GREEN}✅ Infrastructure deployment completed successfully!${NC}"

# Create post-deployment checklist
cat > deployment-checklist.md << EOF
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
- Application: http://$ALB_DNS
- AWS Console: https://console.aws.amazon.com/
- GitHub Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas

## Generated on: $(date)
EOF

print_status "Deployment checklist created: deployment-checklist.md"
