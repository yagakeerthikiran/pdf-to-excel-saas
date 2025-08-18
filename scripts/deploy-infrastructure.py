#!/usr/bin/env python3
"""
Infrastructure Deployment Script - Sydney Region (ap-southeast-2)
"""

import os
import sys
import subprocess
import json
import time
import secrets
import string
from datetime import datetime

AWS_REGION = "ap-southeast-2"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_status(msg): print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")
def print_error(msg): print(f"{Colors.RED}❌ {msg}{Colors.END}")
def print_info(msg): print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def run_command(cmd, capture=False, cwd=None):
    if not capture: print_info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, cwd=cwd)
    return result.returncode == 0, result.stdout, result.stderr

def check_prerequisites():
    print_info("Checking prerequisites...")
    tools = ['aws', 'terraform', 'docker', 'python']
    for tool in tools:
        success, _, _ = run_command(f'{tool} --version', capture=True)
        if success:
            print_status(f"{tool} installed")
        else:
            print_error(f"{tool} not found")
            return False
    return True

def create_terraform_bucket():
    print_info("Setting up Terraform state bucket...")
    bucket_name = f"pdf-excel-saas-terraform-state"
    
    # Try to create bucket
    success, _, _ = run_command(f'aws s3 mb s3://{bucket_name} --region {AWS_REGION}', capture=True)
    if not success:
        # Try with account ID
        account_result = run_command('aws sts get-caller-identity', capture=True)
        if account_result[0]:
            account_id = json.loads(account_result[1])['Account']
            bucket_name = f"pdf-excel-saas-terraform-state-{account_id}"
            run_command(f'aws s3 mb s3://{bucket_name} --region {AWS_REGION}')
    
    # Create backend config
    os.makedirs('infra', exist_ok=True)
    with open('infra/backend.tf', 'w') as f:
        f.write(f'''terraform {{
  backend "s3" {{
    bucket = "{bucket_name}"
    key    = "terraform.tfstate"
    region = "{AWS_REGION}"
  }}
}}
''')
    print_status(f"Created backend config for bucket: {bucket_name}")
    return True

def deploy_infrastructure():
    print_info("Deploying infrastructure...")
    if not os.path.exists('infra'):
        print_error("infra directory not found")
        return False
    
    success, _, _ = run_command('terraform init', cwd='infra')
    if not success: return False
    
    success, _, _ = run_command(f'terraform plan -var="aws_region={AWS_REGION}" -out=tfplan', cwd='infra')
    if not success: return False
    
    confirm = input("Deploy infrastructure? This will create AWS resources. (y/N): ")
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled")
        return False
    
    success, _, _ = run_command('terraform apply tfplan', cwd='infra')
    return success

def setup_containers():
    print_info("Setting up containers...")
    
    # Get account ID for ECR
    success, stdout, _ = run_command('aws sts get-caller-identity', capture=True)
    if not success: return False
    
    account_id = json.loads(stdout)['Account']
    ecr_base = f"{account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com"
    
    # Create ECR repos
    for repo in ['pdf-excel-saas-frontend', 'pdf-excel-saas-backend']:
        run_command(f'aws ecr create-repository --repository-name {repo} --region {AWS_REGION}', capture=True)
    
    # Docker login
    success, _, _ = run_command(f'aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {ecr_base}')
    if not success: return False
    
    print_status("Container repositories ready")
    return True

def main():
    print_info(f"🚀 Starting PDF to Excel SaaS Deployment - Region: {AWS_REGION}")
    
    if not check_prerequisites():
        sys.exit(1)
    
    if not create_terraform_bucket():
        sys.exit(1)
    
    if not deploy_infrastructure():
        sys.exit(1)
    
    if not setup_containers():
        sys.exit(1)
    
    print_status("🎉 Deployment completed successfully!")
    print_info("Next: Build and push your Docker containers")

if __name__ == "__main__":
    main()
