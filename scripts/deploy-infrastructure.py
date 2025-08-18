#!/usr/bin/env python3
"""
Infrastructure Deployment Script - Sydney Region (ap-southeast-2)
Resume-safe deployment script for PDF to Excel SaaS
"""

import os
import sys
import subprocess
import json
import time
import secrets
import string
from datetime import datetime
from pathlib import Path

AWS_REGION = "ap-southeast-2"
APP_NAME = "pdf-excel-saas"
ENVIRONMENT = "prod"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(msg): 
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_warning(msg): 
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_error(msg): 
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg): 
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def print_title(msg):
    print(f"\n{Colors.BLUE}🚀 {msg}{Colors.END}")
    print("=" * (len(msg) + 4))

def run_command(cmd, capture=False, cwd=None, check=True):
    """Run command with error handling"""
    if not capture: 
        print_info(f"Running: {cmd}")
    
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=capture, 
        text=True, 
        cwd=cwd
    )
    
    if check and result.returncode != 0:
        if capture:
            print_error(f"Command failed: {cmd}")
            if result.stderr:
                print(f"Error: {result.stderr}")
        return False, result.stdout, result.stderr
    
    return result.returncode == 0, result.stdout, result.stderr

def check_prerequisites():
    """Check if all required tools are installed"""
    print_title("Checking Prerequisites")
    
    tools = {
        'aws': 'AWS CLI - https://aws.amazon.com/cli/',
        'terraform': 'Terraform - https://terraform.io/downloads',
        'python': 'Python 3 - https://python.org/',
        'docker': 'Docker - https://docker.com/ (optional for images)'
    }
    
    missing_tools = []
    
    for tool, url in tools.items():
        success, _, _ = run_command(f'{tool} --version', capture=True, check=False)
        if success:
            print_status(f"{tool} installed")
        else:
            print_error(f"{tool} not found - {url}")
            if tool != 'docker':  # Docker is optional
                missing_tools.append(tool)
    
    if missing_tools:
        print_error(f"Please install missing tools: {', '.join(missing_tools)}")
        return False
    
    # Check AWS credentials
    success, stdout, _ = run_command(
        f'aws sts get-caller-identity --region {AWS_REGION}', 
        capture=True, 
        check=False
    )
    
    if success:
        account_info = json.loads(stdout)
        print_status(f"AWS credentials valid - Account: {account_info['Account']}")
        return True
    else:
        print_error("AWS credentials not configured. Run 'aws configure' first.")
        return False

def validate_environment():
    """Validate environment configuration"""
    print_title("Validating Environment Configuration")
    
    # Check if .env.prod exists
    if not Path('.env.prod').exists():
        print_warning(".env.prod not found")
        
        if Path('.env.prod.template').exists():
            print_info("Creating .env.prod from template...")
            
            # Copy template
            with open('.env.prod.template', 'r') as src:
                content = src.read()
            
            with open('.env.prod', 'w') as dst:
                dst.write(content)
            
            print_warning("Please edit .env.prod with your actual values before continuing.")
            print_info("Opening .env.prod for editing...")
            
            # Try to open with default editor
            if os.name == 'nt':  # Windows
                os.system('notepad .env.prod')
            else:  # Unix-like
                os.system('${EDITOR:-nano} .env.prod')
            
            input("Press Enter when you've updated .env.prod with real values...")
        else:
            print_error(".env.prod.template not found!")
            return False
    
    # Run validation script
    if Path('scripts/validate_env.py').exists():
        print_info("Running environment validation...")
        success, _, _ = run_command(
            'python scripts/validate_env.py --env production --file .env.prod',
            check=False
        )
        
        if success:
            print_status("Environment validation passed")
            return True
        else:
            print_error("Environment validation failed. Please fix the issues above.")
            return False
    else:
        print_warning("Validation script not found. Skipping validation.")
        return True

def create_terraform_state_bucket():
    """Create S3 bucket for Terraform state (resume-safe)"""
    print_title("Setting up Terraform State Storage")
    
    # Get account ID for unique bucket name
    success, stdout, _ = run_command(
        f'aws sts get-caller-identity --region {AWS_REGION}', 
        capture=True
    )
    
    if not success:
        print_error("Could not get AWS account ID")
        return None
    
    account_id = json.loads(stdout)['Account']
    bucket_name = f"{APP_NAME}-terraform-state-{account_id}"
    
    # Check if bucket already exists
    success, _, _ = run_command(
        f'aws s3api head-bucket --bucket {bucket_name} --region {AWS_REGION}',
        capture=True,
        check=False
    )
    
    if success:
        print_status(f"Terraform state bucket already exists: {bucket_name}")
        return bucket_name
    
    # Create bucket
    print_info(f"Creating Terraform state bucket: {bucket_name}")
    success, _, _ = run_command(
        f'aws s3 mb s3://{bucket_name} --region {AWS_REGION}'
    )
    
    if not success:
        print_warning("Could not create state bucket. Using local state.")
        return None
    
    # Configure bucket
    print_info("Configuring bucket encryption and versioning...")
    
    # Enable versioning
    run_command(
        f'aws s3api put-bucket-versioning --bucket {bucket_name} '
        f'--versioning-configuration Status=Enabled --region {AWS_REGION}',
        capture=True
    )
    
    # Enable encryption
    encryption_config = {
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }
    
    with open('/tmp/encryption.json', 'w') as f:
        json.dump(encryption_config, f)
    
    run_command(
        f'aws s3api put-bucket-encryption --bucket {bucket_name} '
        f'--server-side-encryption-configuration file:///tmp/encryption.json '
        f'--region {AWS_REGION}',
        capture=True
    )
    
    # Clean up temp file
    try:
        os.remove('/tmp/encryption.json')
    except:
        pass
    
    print_status(f"Terraform state bucket created: {bucket_name}")
    return bucket_name

def setup_terraform_backend(bucket_name):
    """Setup Terraform backend configuration"""
    if not bucket_name:
        print_warning("No state bucket available. Using local state.")
        return True
    
    # Create infra directory if it doesn't exist
    os.makedirs('infra', exist_ok=True)
    
    # Create backend configuration
    backend_config = f'''terraform {{
  backend "s3" {{
    bucket         = "{bucket_name}"
    key            = "terraform.tfstate"
    region         = "{AWS_REGION}"
    encrypt        = true
  }}
}}
'''
    
    with open('infra/backend.tf', 'w') as f:
        f.write(backend_config)
    
    print_status("Terraform backend configuration created")
    return True

def deploy_infrastructure():
    """Deploy infrastructure with Terraform (resume-safe)"""
    print_title("Deploying Infrastructure with Terraform")
    
    if not Path('infra').exists():
        print_error("infra directory not found")
        return False
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    success, _, _ = run_command('terraform init', cwd='infra')
    if not success:
        print_error("Terraform init failed")
        return False
    
    # Plan deployment
    print_info("Planning infrastructure deployment...")
    success, _, _ = run_command(
        f'terraform plan '
        f'-var="aws_region={AWS_REGION}" '
        f'-var="environment={ENVIRONMENT}" '
        f'-var="app_name={APP_NAME}" '
        f'-out=tfplan',
        cwd='infra'
    )
    
    if not success:
        print_error("Terraform plan failed")
        return False
    
    # Show plan summary
    print_info("Terraform plan summary:")
    success, stdout, _ = run_command(
        'terraform show -no-color tfplan',
        capture=True,
        cwd='infra',
        check=False
    )
    
    if stdout:
        # Extract plan summary
        lines = stdout.split('\n')
        for line in lines:
            if 'Plan:' in line or 'will be created' in line or 'will be updated' in line or 'will be destroyed' in line:
                print(line)
    
    # Confirm deployment
    print(f"\n{Colors.YELLOW}⚠️  This will create AWS resources in Sydney ({AWS_REGION}) that may incur costs.{Colors.END}")
    confirm = input("Do you want to proceed with the deployment? (y/N): ")
    
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled by user")
        return False
    
    # Apply configuration
    print_info("Applying Terraform configuration...")
    success, _, _ = run_command('terraform apply tfplan', cwd='infra')
    
    if success:
        print_status("Infrastructure deployment completed!")
        capture_terraform_outputs()
        return True
    else:
        print_error("Infrastructure deployment failed!")
        return False

def capture_terraform_outputs():
    """Capture and save Terraform outputs"""
    print_info("Capturing infrastructure outputs...")
    
    outputs = {}
    output_keys = [
        'alb_dns_name',
        's3_bucket_name', 
        'ecr_frontend_url',
        'ecr_backend_url',
        'database_endpoint',
        'vpc_id',
        'ecs_cluster_name'
    ]
    
    for key in output_keys:
        success, stdout, _ = run_command(
            f'terraform output -raw {key}',
            capture=True,
            cwd='infra',
            check=False
        )
        
        if success and stdout.strip():
            outputs[key] = stdout.strip()
        else:
            outputs[key] = "N/A"
    
    # Get account ID
    success, stdout, _ = run_command(
        f'aws sts get-caller-identity --region {AWS_REGION}',
        capture=True
    )
    
    if success:
        account_id = json.loads(stdout)['Account']
        outputs['aws_account_id'] = account_id
    
    outputs['aws_region'] = AWS_REGION
    outputs['environment'] = ENVIRONMENT
    outputs['app_name'] = APP_NAME
    outputs['deployment_time'] = datetime.now().isoformat()
    
    # Save to file
    with open('infrastructure-outputs.json', 'w') as f:
        json.dump(outputs, f, indent=2)
    
    # Also save as env format
    env_content = []
    for key, value in outputs.items():
        env_key = key.upper()
        env_content.append(f"{env_key}={value}")
    
    with open('infrastructure-outputs.env', 'w') as f:
        f.write('\n'.join(env_content))
    
    print_status("Infrastructure outputs saved to infrastructure-outputs.json and .env")
    
    # Display key outputs
    print(f"\n{Colors.CYAN}📊 Key Infrastructure Outputs:{Colors.END}")
    if outputs.get('alb_dns_name', 'N/A') != 'N/A':
        print(f"• Load Balancer: {outputs['alb_dns_name']}")
    if outputs.get('s3_bucket_name', 'N/A') != 'N/A':
        print(f"• S3 Bucket: {outputs['s3_bucket_name']}")
    if outputs.get('ecr_frontend_url', 'N/A') != 'N/A':
        print(f"• Frontend ECR: {outputs['ecr_frontend_url']}")
    if outputs.get('ecr_backend_url', 'N/A') != 'N/A':
        print(f"• Backend ECR: {outputs['ecr_backend_url']}")

def setup_container_repositories():
    """Setup ECR repositories (resume-safe)"""
    print_title("Setting up Container Repositories")
    
    repositories = ['pdf-excel-saas-frontend', 'pdf-excel-saas-backend']
    
    for repo in repositories:
        # Check if repository exists
        success, _, _ = run_command(
            f'aws ecr describe-repositories --repository-names {repo} --region {AWS_REGION}',
            capture=True,
            check=False
        )
        
        if success:
            print_status(f"ECR repository already exists: {repo}")
        else:
            print_info(f"Creating ECR repository: {repo}")
            success, _, _ = run_command(
                f'aws ecr create-repository --repository-name {repo} '
                f'--image-scanning-configuration scanOnPush=true --region {AWS_REGION}'
            )
            
            if success:
                print_status(f"ECR repository created: {repo}")
            else:
                print_warning(f"Could not create ECR repository: {repo}")
    
    return True

def docker_login_ecr():
    """Login to ECR for Docker operations"""
    print_info("Logging into ECR...")
    
    # Get account ID
    success, stdout, _ = run_command(
        f'aws sts get-caller-identity --region {AWS_REGION}',
        capture=True
    )
    
    if not success:
        print_error("Could not get AWS account ID")
        return False
    
    account_id = json.loads(stdout)['Account']
    ecr_url = f"{account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com"
    
    # Get login password and login
    success, _, _ = run_command(
        f'aws ecr get-login-password --region {AWS_REGION} | '
        f'docker login --username AWS --password-stdin {ecr_url}'
    )
    
    if success:
        print_status("Docker login to ECR successful")
        return True
    else:
        print_warning("Docker login to ECR failed. You can build images later.")
        return False

def create_deployment_summary():
    """Create deployment summary and next steps"""
    print_title("Deployment Summary")
    
    summary = f"""# PDF to Excel SaaS - Deployment Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Infrastructure Status
✅ AWS VPC and networking (Sydney - {AWS_REGION})
✅ RDS PostgreSQL database
✅ S3 bucket for file storage  
✅ ECS cluster for containers
✅ Application Load Balancer
✅ ECR repositories
✅ CloudWatch logging
✅ Security groups and IAM roles

## Next Steps
□ Build and push Docker images
□ Update GitHub secrets for CI/CD
□ Configure domain DNS (if applicable)
□ Set up SSL certificate
□ Test application deployment
□ Configure monitoring alerts
□ Run security audit

## Important Files
- infrastructure-outputs.json: All Terraform outputs
- infrastructure-outputs.env: Environment variables format
- .env.prod: Production environment configuration

## Commands to Build Images
```bash
# Frontend
docker build -f frontend/Dockerfile.prod -t pdf-excel-saas-frontend frontend/
docker tag pdf-excel-saas-frontend:latest <ECR_FRONTEND_URL>:latest
docker push <ECR_FRONTEND_URL>:latest

# Backend  
docker build -f backend/Dockerfile.prod -t pdf-excel-saas-backend backend/
docker tag pdf-excel-saas-backend:latest <ECR_BACKEND_URL>:latest
docker push <ECR_BACKEND_URL>:latest
```

## Useful Links
- AWS Console (Sydney): https://ap-southeast-2.console.aws.amazon.com/
- GitHub Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas
"""
    
    with open('deployment-summary.md', 'w') as f:
        f.write(summary)
    
    print_status("Deployment summary saved to deployment-summary.md")

def main():
    """Main deployment function"""
    print(f"{Colors.BLUE}")
    print("🚀 PDF to Excel SaaS - Infrastructure Deployment")
    print("================================================")
    print(f"Region: {AWS_REGION} (Sydney, Australia)")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Application: {APP_NAME}")
    print(f"{Colors.END}")
    
    try:
        # Step 1: Check prerequisites
        if not check_prerequisites():
            print_error("Prerequisites check failed")
            sys.exit(1)
        
        # Step 2: Validate environment
        if not validate_environment():
            print_error("Environment validation failed")
            sys.exit(1)
        
        # Step 3: Create Terraform state bucket
        bucket_name = create_terraform_state_bucket()
        
        # Step 4: Setup Terraform backend
        if not setup_terraform_backend(bucket_name):
            print_error("Terraform backend setup failed")
            sys.exit(1)
        
        # Step 5: Deploy infrastructure
        if not deploy_infrastructure():
            print_error("Infrastructure deployment failed")
            sys.exit(1)
        
        # Step 6: Setup container repositories
        if not setup_container_repositories():
            print_warning("Container repository setup had issues")
        
        # Step 7: Docker login (optional)
        docker_login_ecr()
        
        # Step 8: Create summary
        create_deployment_summary()
        
        print(f"\n{Colors.GREEN}🎉 Infrastructure deployment completed successfully!{Colors.END}")
        print(f"\n{Colors.CYAN}📋 Next Steps:{Colors.END}")
        print("1. Check deployment-summary.md for detailed next steps")
        print("2. Build and push Docker images to ECR")
        print("3. Configure GitHub secrets for CI/CD")
        print("4. Test your application endpoints")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Deployment interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
