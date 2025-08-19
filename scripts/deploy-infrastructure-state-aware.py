#!/usr/bin/env python3
"""
AWS State-Aware Infrastructure Deployment Script
- Always checks actual AWS resources instead of cached outputs
- Resume-safe deployment with real-time state verification
- Windows optimized with proper error handling
"""

import os
import sys
import subprocess
import json
import time
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

def run_aws_command(cmd, description=""):
    """Run AWS CLI command and return parsed JSON result"""
    if description:
        print_info(f"Checking: {description}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    return True, json.loads(result.stdout)
                except json.JSONDecodeError:
                    return True, result.stdout.strip()
            return True, None
        else:
            return False, result.stderr.strip() if result.stderr else "Command failed"
            
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def run_terraform_command(cmd, cwd='infra', description=""):
    """Run Terraform command with proper error handling"""
    if description:
        print_info(f"Terraform: {description}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            timeout=300
        )
        
        success = result.returncode == 0
        
        if not success:
            print_error(f"Terraform command failed: {cmd}")
            if result.stderr:
                print(f"Error: {result.stderr}")
        
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print_error("Terraform command timed out")
        return False, "", "Timeout"
    except Exception as e:
        print_error(f"Terraform command execution failed: {e}")
        return False, "", str(e)

def get_aws_account_info():
    """Get current AWS account information"""
    print_title("Checking AWS Account Information")
    
    success, result = run_aws_command(
        f'aws sts get-caller-identity --region {AWS_REGION}',
        "AWS account identity"
    )
    
    if success and isinstance(result, dict):
        account_id = result['Account']
        user_arn = result.get('Arn', 'Unknown')
        print_status(f"AWS Account: {account_id}")
        print_status(f"User: {user_arn}")
        return account_id
    else:
        print_error("AWS credentials not configured or invalid")
        print_info("Please run: aws configure")
        print_info("Set region to: ap-southeast-2")
        return None

def check_s3_bucket_exists(bucket_name):
    """Check if S3 bucket exists"""
    success, result = run_aws_command(
        f'aws s3api head-bucket --bucket {bucket_name} --region {AWS_REGION}',
        f"S3 bucket: {bucket_name}"
    )
    return success

def check_rds_instance_exists(db_identifier):
    """Check if RDS instance exists"""
    success, result = run_aws_command(
        f'aws rds describe-db-instances --db-instance-identifier {db_identifier} --region {AWS_REGION}',
        f"RDS instance: {db_identifier}"
    )
    return success

def check_ecs_cluster_exists(cluster_name):
    """Check if ECS cluster exists"""
    success, result = run_aws_command(
        f'aws ecs describe-clusters --clusters {cluster_name} --region {AWS_REGION}',
        f"ECS cluster: {cluster_name}"
    )
    
    if success and isinstance(result, dict):
        clusters = result.get('clusters', [])
        if clusters and clusters[0].get('status') == 'ACTIVE':
            return True
    return False

def check_ecr_repository_exists(repo_name):
    """Check if ECR repository exists"""
    success, result = run_aws_command(
        f'aws ecr describe-repositories --repository-names {repo_name} --region {AWS_REGION}',
        f"ECR repository: {repo_name}"
    )
    return success

def check_load_balancer_exists(lb_name):
    """Check if Application Load Balancer exists"""
    success, result = run_aws_command(
        f'aws elbv2 describe-load-balancers --region {AWS_REGION}',
        "Application Load Balancers"
    )
    
    if success and isinstance(result, dict):
        load_balancers = result.get('LoadBalancers', [])
        for lb in load_balancers:
            if lb_name in lb.get('LoadBalancerName', ''):
                return True, lb.get('DNSName')
    return False, None

def check_vpc_exists():
    """Check for existing VPC with our tags"""
    success, result = run_aws_command(
        f'aws ec2 describe-vpcs --filters "Name=tag:Name,Values=pdf-excel-saas-*" --region {AWS_REGION}',
        "VPC infrastructure"
    )
    
    if success and isinstance(result, dict):
        vpcs = result.get('Vpcs', [])
        return len(vpcs) > 0, vpcs
    return False, []

def get_current_infrastructure_state(account_id):
    """Get complete current state of AWS infrastructure"""
    print_title("Checking Current AWS Infrastructure State")
    
    state = {
        'account_id': account_id,
        'region': AWS_REGION,
        'timestamp': datetime.now().isoformat()
    }
    
    # Check S3 buckets
    app_bucket = f"{APP_NAME}-{ENVIRONMENT}"
    state_bucket = f"{APP_NAME}-tfstate-{account_id}"
    
    state['s3'] = {
        'app_bucket': {
            'name': app_bucket,
            'exists': check_s3_bucket_exists(app_bucket)
        },
        'state_bucket': {
            'name': state_bucket,
            'exists': check_s3_bucket_exists(state_bucket)
        }
    }
    
    # Check RDS
    db_identifier = f"{APP_NAME}-{ENVIRONMENT}-db"
    state['rds'] = {
        'identifier': db_identifier,
        'exists': check_rds_instance_exists(db_identifier)
    }
    
    # Check ECS
    cluster_name = f"{APP_NAME}-{ENVIRONMENT}"
    state['ecs'] = {
        'cluster_name': cluster_name,
        'exists': check_ecs_cluster_exists(cluster_name)
    }
    
    # Check ECR repositories
    state['ecr'] = {
        'frontend': {
            'name': f"{APP_NAME}-frontend",
            'exists': check_ecr_repository_exists(f"{APP_NAME}-frontend")
        },
        'backend': {
            'name': f"{APP_NAME}-backend",
            'exists': check_ecr_repository_exists(f"{APP_NAME}-backend")
        }
    }
    
    # Check Load Balancer
    lb_exists, lb_dns = check_load_balancer_exists(APP_NAME)
    state['load_balancer'] = {
        'exists': lb_exists,
        'dns_name': lb_dns
    }
    
    # Check VPC
    vpc_exists, vpcs = check_vpc_exists()
    state['vpc'] = {
        'exists': vpc_exists,
        'count': len(vpcs)
    }
    
    return state

def display_infrastructure_summary(state):
    """Display current infrastructure state"""
    print_title("Current Infrastructure Summary")
    
    print(f"AWS Account: {state['account_id']}")
    print(f"Region: {state['region']}")
    print(f"Checked at: {state['timestamp']}")
    
    print(f"\n{Colors.CYAN}S3 Storage:{Colors.END}")
    app_bucket = state['s3']['app_bucket']
    state_bucket = state['s3']['state_bucket']
    
    status = "✅ EXISTS" if app_bucket['exists'] else "❌ MISSING"
    print(f"  Application Bucket ({app_bucket['name']}): {status}")
    
    status = "✅ EXISTS" if state_bucket['exists'] else "❌ MISSING"
    print(f"  Terraform State ({state_bucket['name']}): {status}")
    
    print(f"\n{Colors.CYAN}Compute & Database:{Colors.END}")
    
    status = "✅ EXISTS" if state['rds']['exists'] else "❌ MISSING"
    print(f"  RDS Database ({state['rds']['identifier']}): {status}")
    
    status = "✅ EXISTS" if state['ecs']['exists'] else "❌ MISSING"
    print(f"  ECS Cluster ({state['ecs']['cluster_name']}): {status}")
    
    print(f"\n{Colors.CYAN}Container Registries:{Colors.END}")
    for repo_type, repo_info in state['ecr'].items():
        status = "✅ EXISTS" if repo_info['exists'] else "❌ MISSING"
        print(f"  ECR {repo_type.title()} ({repo_info['name']}): {status}")
    
    print(f"\n{Colors.CYAN}Networking:{Colors.END}")
    status = "✅ EXISTS" if state['vpc']['exists'] else "❌ MISSING"
    print(f"  VPC Infrastructure: {status}")
    
    if state['load_balancer']['exists']:
        print(f"  Load Balancer: ✅ EXISTS")
        print(f"  Load Balancer DNS: {state['load_balancer']['dns_name']}")
    else:
        print(f"  Load Balancer: ❌ MISSING")
    
    # Calculate deployment status
    components = [
        state['s3']['app_bucket']['exists'],
        state['rds']['exists'],
        state['ecs']['exists'],
        state['ecr']['frontend']['exists'],
        state['ecr']['backend']['exists'],
        state['vpc']['exists'],
        state['load_balancer']['exists']
    ]
    
    deployed_count = sum(components)
    total_count = len(components)
    
    print(f"\n{Colors.BLUE}Deployment Status: {deployed_count}/{total_count} components deployed{Colors.END}")
    
    if deployed_count == total_count:
        print_status("Infrastructure is FULLY DEPLOYED")
        return "complete"
    elif deployed_count > 0:
        print_warning("Infrastructure is PARTIALLY DEPLOYED")
        return "partial"
    else:
        print_info("Infrastructure is NOT DEPLOYED")
        return "none"

def setup_terraform_backend(account_id, state):
    """Setup Terraform backend based on current state"""
    print_title("Setting up Terraform Backend")
    
    state_bucket_name = f"{APP_NAME}-tfstate-{account_id}"
    
    # Create state bucket if it doesn't exist
    if not state['s3']['state_bucket']['exists']:
        print_info(f"Creating Terraform state bucket: {state_bucket_name}")
        
        success, result = run_aws_command(
            f'aws s3 mb s3://{state_bucket_name} --region {AWS_REGION}',
            f"Creating state bucket"
        )
        
        if success:
            print_status("State bucket created successfully")
            
            # Enable versioning
            run_aws_command(
                f'aws s3api put-bucket-versioning --bucket {state_bucket_name} '
                f'--versioning-configuration Status=Enabled --region {AWS_REGION}',
                "Enabling bucket versioning"
            )
            
            # Enable encryption
            encryption_config = {
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }
            
            with open('temp_encryption.json', 'w') as f:
                json.dump(encryption_config, f)
            
            run_aws_command(
                f'aws s3api put-bucket-encryption --bucket {state_bucket_name} '
                f'--server-side-encryption-configuration file://temp_encryption.json '
                f'--region {AWS_REGION}',
                "Enabling bucket encryption"
            )
            
            os.remove('temp_encryption.json')
            
        else:
            print_warning("Could not create state bucket, using local state")
            # Remove backend config for local state
            backend_file = Path('infra/backend.tf')
            if backend_file.exists():
                backend_file.unlink()
                print_info("Removed backend config - using local state")
            return True
    
    else:
        print_status(f"State bucket already exists: {state_bucket_name}")
    
    # Create backend configuration
    os.makedirs('infra', exist_ok=True)
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
    
    print_status("Backend configuration ready")
    return True

def initialize_terraform():
    """Initialize Terraform with comprehensive error handling"""
    print_title("Initializing Terraform")
    
    # Clean up any problematic state
    terraform_dir = Path('infra/.terraform')
    lock_file = Path('infra/.terraform.lock.hcl')
    
    if terraform_dir.exists():
        print_info("Cleaning up existing Terraform state...")
        import shutil
        shutil.rmtree(terraform_dir)
    
    if lock_file.exists():
        lock_file.unlink()
    
    # Initialize with reconfigure to avoid backend issues
    success, stdout, stderr = run_terraform_command(
        'terraform init -reconfigure',
        description="Initializing with clean state"
    )
    
    if success:
        print_status("Terraform initialized successfully")
        return True
    else:
        print_error("Terraform initialization failed")
        return False

def plan_infrastructure():
    """Plan Terraform deployment"""
    print_title("Planning Infrastructure Deployment")
    
    success, stdout, stderr = run_terraform_command(
        f'terraform plan '
        f'-var="aws_region={AWS_REGION}" '
        f'-var="environment={ENVIRONMENT}" '
        f'-var="app_name={APP_NAME}" '
        f'-out=tfplan',
        description="Planning deployment"
    )
    
    if success:
        # Extract plan summary
        if stdout:
            lines = stdout.split('\n')
            plan_lines = [line for line in lines if any(keyword in line for keyword in 
                         ['Plan:', 'will be created', 'will be updated', 'will be destroyed', 'No changes'])]
            
            if plan_lines:
                print_info("Plan Summary:")
                for line in plan_lines:
                    print(f"  {line}")
        
        return True
    else:
        return False

def apply_infrastructure():
    """Apply Terraform configuration"""
    print_title("Applying Infrastructure Configuration")
    
    print(f"{Colors.YELLOW}[WARNING] This will create/modify AWS resources that may incur costs.{Colors.END}")
    confirm = input("Do you want to proceed? (y/N): ")
    
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled by user")
        return False
    
    success, stdout, stderr = run_terraform_command(
        'terraform apply tfplan',
        description="Applying configuration"
    )
    
    if success:
        print_status("Infrastructure deployment completed!")
        return True
    else:
        print_error("Infrastructure deployment failed!")
        return False

def get_live_terraform_outputs():
    """Get live Terraform outputs and save them"""
    print_title("Capturing Live Infrastructure Outputs")
    
    outputs = {}
    output_keys = [
        'vpc_id', 'alb_dns_name', 's3_bucket_name', 
        'ecr_frontend_url', 'ecr_backend_url', 
        'database_endpoint', 'database_url', 'ecs_cluster_name'
    ]
    
    for key in output_keys:
        success, stdout, stderr = run_terraform_command(
            f'terraform output -raw {key}',
            description=f"Getting {key}"
        )
        
        if success and stdout.strip():
            outputs[key] = stdout.strip()
            print_status(f"{key}: {outputs[key]}")
        else:
            outputs[key] = "N/A"
            print_warning(f"{key}: Not available")
    
    # Add metadata
    outputs.update({
        'aws_region': AWS_REGION,
        'environment': ENVIRONMENT,
        'app_name': APP_NAME,
        'deployment_time': datetime.now().isoformat(),
        'script_version': 'state-aware-v1.0'
    })
    
    # Save outputs
    with open('infrastructure-outputs.json', 'w') as f:
        json.dump(outputs, f, indent=2)
    
    print_status("Live outputs saved to infrastructure-outputs.json")
    return outputs

def main():
    """Main deployment function with state-aware logic"""
    print(f"{Colors.BLUE}")
    print("=== AWS State-Aware Infrastructure Deployment ===")
    print("================================================")
    print(f"App: {APP_NAME}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {AWS_REGION}")
    print(f"{Colors.END}")
    
    try:
        # Step 1: Get AWS account information
        account_id = get_aws_account_info()
        if not account_id:
            print_error("Cannot proceed without valid AWS credentials")
            return
        
        # Step 2: Check current infrastructure state
        current_state = get_current_infrastructure_state(account_id)
        deployment_status = display_infrastructure_summary(current_state)
        
        # Step 3: Ask user what they want to do based on current state
        if deployment_status == "complete":
            print(f"\n{Colors.GREEN}Infrastructure appears to be fully deployed!{Colors.END}")
            action = input("What would you like to do? (check/update/redeploy/quit): ").lower()
            
            if action in ['q', 'quit']:
                print_info("Exiting...")
                return
            elif action in ['c', 'check']:
                outputs = get_live_terraform_outputs()
                print_status("Infrastructure check completed")
                return
            elif action not in ['u', 'update', 'r', 'redeploy']:
                print_info("No action taken")
                return
        
        elif deployment_status == "partial":
            print(f"\n{Colors.YELLOW}Infrastructure is partially deployed.{Colors.END}")
            action = input("Continue with deployment to complete missing components? (y/N): ")
            if action.lower() != 'y':
                print_info("Deployment cancelled")
                return
        
        else:
            print(f"\n{Colors.CYAN}Ready to deploy infrastructure from scratch.{Colors.END}")
            action = input("Proceed with full deployment? (y/N): ")
            if action.lower() != 'y':
                print_info("Deployment cancelled")
                return
        
        # Step 4: Setup Terraform backend
        if not setup_terraform_backend(account_id, current_state):
            print_error("Backend setup failed")
            return
        
        # Step 5: Initialize Terraform
        if not initialize_terraform():
            print_error("Terraform initialization failed")
            return
        
        # Step 6: Plan deployment
        if not plan_infrastructure():
            print_error("Terraform planning failed")
            return
        
        # Step 7: Apply infrastructure
        if not apply_infrastructure():
            print_error("Infrastructure deployment failed")
            return
        
        # Step 8: Get live outputs
        outputs = get_live_terraform_outputs()
        
        # Step 9: Final state check
        print_title("Post-Deployment Infrastructure Verification")
        final_state = get_current_infrastructure_state(account_id)
        final_status = display_infrastructure_summary(final_state)
        
        if final_status == "complete":
            print(f"\n{Colors.GREEN}🎉 DEPLOYMENT SUCCESSFUL!{Colors.END}")
            print(f"\n{Colors.CYAN}Key Resources Created:{Colors.END}")
            
            if outputs.get('alb_dns_name', 'N/A') != 'N/A':
                print(f"• Application URL: http://{outputs['alb_dns_name']}")
            if outputs.get('s3_bucket_name', 'N/A') != 'N/A':
                print(f"• S3 Bucket: {outputs['s3_bucket_name']}")
            if outputs.get('database_endpoint', 'N/A') != 'N/A':
                print(f"• Database: {outputs['database_endpoint']}")
                
            print(f"\n{Colors.CYAN}Next Steps:{Colors.END}")
            print("1. Build and push Docker images to ECR")
            print("2. Configure environment variables")
            print("3. Deploy application to ECS")
            print("4. Test your application")
        else:
            print_warning("Deployment completed but some components may need attention")
            print_info("Check the infrastructure summary above for details")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Deployment interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
