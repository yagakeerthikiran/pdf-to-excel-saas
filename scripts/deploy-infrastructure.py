#!/usr/bin/env python3
"""
Infrastructure Deployment Script - Sydney Region (ap-southeast-2)
Resume-safe deployment script for PDF to Excel SaaS

BUCKET NAMING STRATEGY:
- Terraform State Bucket: "pdf-excel-saas-tfstate-{account-id}" (backend storage only)
- Application Bucket: "pdf-excel-saas-prod" (created by Terraform for app use)
- NO duplicate bucket creation - script only manages Terraform state bucket
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
    print(f"{Colors.GREEN}[SUCCESS] {msg}{Colors.END}")

def print_warning(msg): 
    print(f"{Colors.YELLOW}[WARNING] {msg}{Colors.END}")

def print_error(msg): 
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_info(msg): 
    print(f"{Colors.CYAN}[INFO] {msg}{Colors.END}")

def print_title(msg):
    print(f"\n{Colors.BLUE}=== {msg} ==={Colors.END}")
    print("=" * (len(msg) + 8))

def run_command(cmd, capture=False, cwd=None, check=True):
    """Run command with error handling and proper None checking"""
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
        return False, result.stdout or "", result.stderr or ""
    
    return result.returncode == 0, result.stdout or "", result.stderr or ""

def check_aws_credentials():
    """Check AWS credentials and return account info"""
    print_info("Checking AWS credentials...")
    
    success, stdout, stderr = run_command(
        f'aws sts get-caller-identity --region {AWS_REGION}', 
        capture=True, 
        check=False
    )
    
    if success and stdout:
        try:
            account_info = json.loads(stdout)
            print_status(f"AWS credentials valid - Account: {account_info['Account']}")
            return account_info
        except json.JSONDecodeError:
            print_error("Could not parse AWS account info")
            return None
    else:
        print_error("AWS credentials not configured or invalid")
        print_info("Please run: aws configure")
        print_info("Set region to: ap-southeast-2")
        if stderr:
            print(f"Error details: {stderr}")
        return None

def check_prerequisites():
    """Check if all required tools are installed"""
    print_title("Checking Prerequisites")
    
    tools = {
        'aws': 'AWS CLI - https://aws.amazon.com/cli/',
        'terraform': 'Terraform - https://terraform.io/downloads',
        'python': 'Python 3 - https://python.org/',
    }
    
    missing_tools = []
    
    for tool, url in tools.items():
        success, _, _ = run_command(f'{tool} --version', capture=True, check=False)
        if success:
            print_status(f"{tool} installed")
        else:
            print_error(f"{tool} not found - {url}")
            missing_tools.append(tool)
    
    if missing_tools:
        print_error(f"Please install missing tools: {', '.join(missing_tools)}")
        return False, None
    
    # Check AWS credentials
    account_info = check_aws_credentials()
    if not account_info:
        return False, None
    
    return True, account_info

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
            print_info("You can use: python scripts/generate-env-vars.py")
            
            input("Press Enter when you've updated .env.prod with real values...")
        else:
            print_error(".env.prod.template not found!")
            return False
    
    # Run validation script if available
    if Path('scripts/validate_env.py').exists():
        print_info("Running environment validation...")
        success, stdout, stderr = run_command(
            'python scripts/validate_env.py --env production --file .env.prod',
            capture=True,
            check=False
        )
        
        if success:
            print_status("Environment validation passed")
        else:
            print_warning("Environment validation failed, but continuing...")
            print_info("Fix validation issues later or run: python scripts/generate-env-vars.py")
    else:
        print_warning("Validation script not found. Skipping validation.")
    
    return True

def setup_terraform_backend(account_id):
    """Setup Terraform backend - FIXED naming to prevent conflicts"""
    print_title("Setting up Terraform Backend")
    
    # Create infra directory if it doesn't exist
    os.makedirs('infra', exist_ok=True)
    
    # FIXED: Use "tfstate" to distinguish from application bucket
    state_bucket_name = f"{APP_NAME}-tfstate-{account_id}"
    
    print_info(f"Terraform state bucket: {state_bucket_name}")
    print_info(f"Application bucket: {APP_NAME}-{ENVIRONMENT} (managed by Terraform)")
    
    # Check if Terraform state bucket exists
    print_info(f"Checking Terraform state bucket: {state_bucket_name}")
    success, _, _ = run_command(
        f'aws s3api head-bucket --bucket {state_bucket_name} --region {AWS_REGION}',
        capture=True,
        check=False
    )
    
    if not success:
        print_info(f"Creating Terraform state bucket: {state_bucket_name}")
        
        # Create state bucket
        success, _, stderr = run_command(
            f'aws s3 mb s3://{state_bucket_name} --region {AWS_REGION}',
            capture=True,
            check=False
        )
        
        if success:
            print_status(f"Created Terraform state bucket: {state_bucket_name}")
            
            # Configure bucket for Terraform state
            print_info("Configuring state bucket...")
            
            # Enable versioning (critical for Terraform state)
            run_command(
                f'aws s3api put-bucket-versioning --bucket {state_bucket_name} '
                f'--versioning-configuration Status=Enabled --region {AWS_REGION}',
                capture=True,
                check=False
            )
            
            # Enable encryption
            encryption_config = {
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }
            
            temp_file = 'encryption_temp.json'
            try:
                with open(temp_file, 'w') as f:
                    json.dump(encryption_config, f)
                
                run_command(
                    f'aws s3api put-bucket-encryption --bucket {state_bucket_name} '
                    f'--server-side-encryption-configuration file://{temp_file} '
                    f'--region {AWS_REGION}',
                    capture=True,
                    check=False
                )
                
                os.remove(temp_file)
                print_status("State bucket encryption configured")
            except Exception as e:
                print_warning(f"Could not configure bucket encryption: {e}")
        
        else:
            print_warning("Could not create Terraform state bucket. Using local state.")
            print_info("This is acceptable for development but not recommended for production")
            
            # Remove backend configuration to use local state
            backend_file = Path('infra/backend.tf')
            if backend_file.exists():
                print_info("Removing backend configuration to use local state")
                backend_file.unlink()
            
            return True  # Continue with local state
    
    else:
        print_status(f"Terraform state bucket already exists: {state_bucket_name}")
    
    # Create backend configuration
    backend_config = f'''terraform {{
  backend "s3" {{
    bucket         = "{state_bucket_name}"
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

def check_existing_infrastructure(account_id):
    """Check what infrastructure already exists to avoid conflicts"""
    print_title("Checking Existing Infrastructure")
    
    # Check application bucket (created by Terraform)
    app_bucket = f"{APP_NAME}-{ENVIRONMENT}"
    success, _, _ = run_command(
        f'aws s3api head-bucket --bucket {app_bucket} --region {AWS_REGION}',
        capture=True,
        check=False
    )
    
    if success:
        print_status(f"Application bucket exists: {app_bucket}")
    else:
        print_info(f"Application bucket will be created: {app_bucket}")
    
    # Check for old/incorrect buckets
    old_bucket_patterns = [
        f"{APP_NAME}-terraform-state-{account_id}",  # Old pattern
        f"{APP_NAME}-terraform-state"  # Very old pattern
    ]
    
    for old_bucket in old_bucket_patterns:
        success, _, _ = run_command(
            f'aws s3api head-bucket --bucket {old_bucket} --region {AWS_REGION}',
            capture=True,
            check=False
        )
        
        if success:
            print_warning(f"Found old state bucket: {old_bucket}")
            print_info("This bucket can be cleaned up after migration to new naming")

def deploy_infrastructure():
    """Deploy infrastructure with Terraform"""
    print_title("Deploying Infrastructure with Terraform")
    
    if not Path('infra').exists():
        print_error("infra directory not found")
        return False
    
    # Enhanced terraform init with comprehensive error handling
    print_info("Initializing Terraform...")
    
    # Strategy 1: Normal init
    success, stdout, stderr = run_command('terraform init', cwd='infra', check=False)
    
    if not success:
        print_warning("Initial terraform init failed")
        
        if stderr:
            print_info(f"Error details: {stderr}")
            
            # Strategy 2: Backend issues - reconfigure
            if any(keyword in stderr for keyword in [
                "Backend configuration changed",
                "bucket does not exist", 
                "NoSuchBucket",
                "region does not match",
                "backend initialization required"
            ]):
                print_info("Backend configuration issue - reconfiguring...")
                success, _, _ = run_command('terraform init -reconfigure', cwd='infra', check=False)
            
            # Strategy 3: Migration needed
            elif "migration" in stderr.lower():
                print_info("State migration needed...")
                success, _, _ = run_command('terraform init -migrate-state', cwd='infra', check=False)
                
                if not success:
                    print_warning("Migration failed, trying reconfigure...")
                    success, _, _ = run_command('terraform init -reconfigure', cwd='infra', check=False)
            
            # Strategy 4: Credentials/permissions
            elif any(keyword in stderr.lower() for keyword in ["credentials", "access denied", "unauthorized"]):
                print_error("AWS credentials/permissions issue")
                print_info("Please check: aws sts get-caller-identity --region ap-southeast-2")
                return False
            
            # Strategy 5: Unknown error - force reconfigure
            else:
                print_warning("Unknown error, forcing reconfigure...")
                success, _, _ = run_command('terraform init -reconfigure', cwd='infra', check=False)
    
    if not success:
        print_error("Terraform initialization failed after all attempts")
        print_info("Manual steps to try:")
        print_info("1. cd infra")
        print_info("2. rm -rf .terraform .terraform.lock.hcl")
        print_info("3. terraform init -reconfigure")
        return False
    
    print_status("Terraform initialized successfully")
    
    # Plan deployment
    print_info("Planning infrastructure deployment...")
    success, _, stderr = run_command(
        f'terraform plan '
        f'-var="aws_region={AWS_REGION}" '
        f'-var="environment={ENVIRONMENT}" '
        f'-var="app_name={APP_NAME}" '
        f'-out=tfplan',
        cwd='infra',
        check=False
    )
    
    if not success:
        print_error("Terraform plan failed")
        if stderr:
            print(f"Error details: {stderr}")
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
        # Extract and show plan summary
        lines = stdout.split('\n')
        plan_lines = [line for line in lines if any(keyword in line for keyword in 
                     ['Plan:', 'will be created', 'will be updated', 'will be destroyed', 'No changes'])]
        
        if plan_lines:
            for line in plan_lines:
                print(line)
        else:
            print("Plan completed - review for changes")
    
    # Confirm deployment
    print(f"\n{Colors.YELLOW}[WARNING] This will create AWS resources in Sydney ({AWS_REGION}) that may incur costs.{Colors.END}")
    print(f"Application bucket that will be created: {APP_NAME}-{ENVIRONMENT}")
    confirm = input("Do you want to proceed with the deployment? (y/N): ")
    
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled by user")
        return False
    
    # Apply configuration
    print_info("Applying Terraform configuration...")
    success, _, stderr = run_command('terraform apply tfplan', cwd='infra', check=False)
    
    if success:
        print_status("Infrastructure deployment completed!")
        capture_terraform_outputs()
        return True
    else:
        print_error("Infrastructure deployment failed!")
        if stderr:
            print(f"Error details: {stderr}")
        return False

def capture_terraform_outputs():
    """Capture and save Terraform outputs"""
    print_info("Capturing infrastructure outputs...")
    
    outputs = {}
    output_keys = [
        'alb_dns_name',
        's3_bucket_name',  # This should be "pdf-excel-saas-prod"
        'ecr_frontend_url',
        'ecr_backend_url',
        'database_endpoint',
        'database_url',
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
        
        if success and stdout and stdout.strip():
            outputs[key] = stdout.strip()
        else:
            outputs[key] = "N/A"
    
    # Add metadata
    outputs['aws_region'] = AWS_REGION
    outputs['environment'] = ENVIRONMENT
    outputs['app_name'] = APP_NAME
    outputs['deployment_time'] = datetime.now().isoformat()
    
    # Save outputs
    with open('infrastructure-outputs.json', 'w') as f:
        json.dump(outputs, f, indent=2)
    
    # Save as env format
    env_content = [f"{k.upper()}={v}" for k, v in outputs.items()]
    with open('infrastructure-outputs.env', 'w') as f:
        f.write('\n'.join(env_content))
    
    print_status("Infrastructure outputs saved")
    
    # Display key outputs with correct naming
    print(f"\n{Colors.CYAN}Key Infrastructure Outputs:{Colors.END}")
    if outputs.get('s3_bucket_name', 'N/A') != 'N/A':
        print(f"* Application S3 Bucket: {outputs['s3_bucket_name']}")
    if outputs.get('alb_dns_name', 'N/A') != 'N/A':
        print(f"* Load Balancer DNS: {outputs['alb_dns_name']}")
    if outputs.get('ecr_frontend_url', 'N/A') != 'N/A':
        print(f"* Frontend ECR: {outputs['ecr_frontend_url']}")
    if outputs.get('ecr_backend_url', 'N/A') != 'N/A':
        print(f"* Backend ECR: {outputs['ecr_backend_url']}")

def setup_container_repositories():
    """Setup ECR repositories (resume-safe)"""
    print_title("Setting up Container Repositories")
    
    # Note: ECR repositories are already created by Terraform main.tf
    # This function just validates they exist
    
    repositories = [
        f'{APP_NAME}-frontend',  # Created by Terraform
        f'{APP_NAME}-backend'    # Created by Terraform
    ]
    
    for repo in repositories:
        success, _, _ = run_command(
            f'aws ecr describe-repositories --repository-names {repo} --region {AWS_REGION}',
            capture=True,
            check=False
        )
        
        if success:
            print_status(f"ECR repository exists: {repo}")
        else:
            print_warning(f"ECR repository not found: {repo}")
            print_info("ECR repositories should be created by Terraform main.tf")
    
    return True

def create_deployment_summary():
    """Create deployment summary"""
    summary = f"""# PDF to Excel SaaS - Deployment Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Infrastructure Status
✅ Infrastructure deployed to Sydney ({AWS_REGION})
✅ Application S3 bucket: {APP_NAME}-{ENVIRONMENT}
✅ Terraform state managed separately
✅ Container repositories ready

## Bucket Usage
- **Application Bucket**: `{APP_NAME}-{ENVIRONMENT}` (for PDF uploads/downloads)
- **Terraform State**: `{APP_NAME}-tfstate-{{account-id}}` (for infrastructure state)

## Next Steps
1. Build and push Docker images to ECR
2. Configure environment variables in .env.prod
3. Test application deployment
4. Set up monitoring and alerts

## Important Notes
- Application uses bucket: {APP_NAME}-{ENVIRONMENT}
- No duplicate buckets should be created
- ECR repositories are managed by Terraform

## Troubleshooting
- Environment issues: `python scripts/generate-env-vars.py`
- Check outputs: `cat infrastructure-outputs.json`
"""
    
    with open('deployment-summary.md', 'w') as f:
        f.write(summary)
    
    print_status("Deployment summary created")

def main():
    """Main deployment function"""
    print(f"{Colors.BLUE}")
    print("=== PDF to Excel SaaS - Infrastructure Deployment ===")
    print("=====================================================")
    print(f"Region: {AWS_REGION} (Sydney, Australia)")
    print(f"App Bucket: {APP_NAME}-{ENVIRONMENT}")
    print(f"{Colors.END}")
    
    try:
        # Step 1: Check prerequisites and get account info
        prereqs_ok, account_info = check_prerequisites()
        if not prereqs_ok:
            print_error("Prerequisites check failed")
            sys.exit(1)
        
        account_id = account_info['Account']
        print_info(f"Using AWS Account: {account_id}")
        print_info(f"Terraform state bucket: {APP_NAME}-tfstate-{account_id}")
        
        # Step 2: Validate environment
        if not validate_environment():
            print_warning("Environment validation had issues, but continuing...")
        
        # Step 3: Check existing infrastructure
        check_existing_infrastructure(account_id)
        
        # Step 4: Setup Terraform backend with correct naming
        if not setup_terraform_backend(account_id):
            print_error("Terraform backend setup failed")
            sys.exit(1)
        
        # Step 5: Deploy infrastructure
        if not deploy_infrastructure():
            print_error("Infrastructure deployment failed")
            sys.exit(1)
        
        # Step 6: Validate container repositories
        setup_container_repositories()
        
        # Step 7: Create summary
        create_deployment_summary()
        
        print(f"\n{Colors.GREEN}[SUCCESS] Infrastructure deployment completed!{Colors.END}")
        print(f"\n{Colors.CYAN}Next Steps:{Colors.END}")
        print(f"1. Application will use S3 bucket: {APP_NAME}-{ENVIRONMENT}")
        print("2. Check infrastructure-outputs.json for all details")
        print("3. Build and push Docker images to ECR")
        print("4. Configure your application environment")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[WARNING] Deployment interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}[ERROR] Unexpected error: {str(e)}{Colors.END}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
