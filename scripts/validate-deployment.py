#!/usr/bin/env python3
"""
🔍 PRE-DEPLOYMENT VALIDATION SCRIPT
==================================

Quick validation to ensure everything is ready for deployment.
Run this before executing the go-live script.
"""

import subprocess
import json
import sys
import os
from pathlib import Path
from typing import Tuple, List

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def print_header():
    print(f"\n{Colors.BLUE}{Colors.BOLD}")
    print("🔍 PDF TO EXCEL SAAS - DEPLOYMENT READINESS CHECK")
    print("=" * 50)
    print(f"{Colors.END}")

def run_command(cmd: str, cwd: str = None) -> Tuple[bool, str, str]:
    """Run command and return success, stdout, stderr"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_required_files() -> List[str]:
    """Check all required files exist"""
    print_info("Checking required project files...")
    
    required_files = [
        # Scripts
        'scripts/deploy-infrastructure.py',
        'scripts/deploy-application.py',
        'scripts/go-live.py',
        'scripts/validate_env.py',
        
        # Infrastructure
        'infra/main.tf',
        
        # Backend
        'backend/main.py',
        'backend/Dockerfile',
        'backend/requirements.txt',
        'backend/conversion_service.py',
        'backend/file_service.py',
        'backend/email_service.py',
        
        # Frontend
        'frontend/package.json',
        'frontend/Dockerfile',
        'frontend/next.config.js',
        'frontend/src/app/page.tsx',
        'frontend/src/app/layout.tsx',
        
        # Configuration
        '.env.prod.template',
        'env.schema.json'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    print_success(f"Found {len(existing_files)} required files")
    
    if missing_files:
        print_warning("Missing files:")
        for file in missing_files:
            print(f"   ❌ {file}")
    
    return missing_files

def check_environment_setup() -> bool:
    """Check environment configuration"""
    print_info("Checking environment setup...")
    
    env_prod_exists = Path('.env.prod').exists()
    env_template_exists = Path('.env.prod.template').exists()
    
    if env_prod_exists:
        print_success(".env.prod file exists")
        
        # Check if it has basic required variables
        with open('.env.prod', 'r') as f:
            content = f.read()
            
        required_vars = ['AWS_REGION', 'AWS_ACCOUNT_ID', 'DATABASE_URL']
        missing_vars = []
        
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print_warning(f"Missing environment variables: {', '.join(missing_vars)}")
            return False
        else:
            print_success("Required environment variables present")
            return True
            
    elif env_template_exists:
        print_warning(".env.prod not found, but template exists")
        print_info("Run: cp .env.prod.template .env.prod")
        print_info("Then edit .env.prod with your actual values")
        return False
    else:
        print_error("No environment configuration found")
        return False

def check_aws_setup() -> bool:
    """Check AWS CLI and credentials"""
    print_info("Checking AWS setup...")
    
    # Check AWS CLI
    success, stdout, stderr = run_command("aws --version")
    if not success:
        print_error("AWS CLI not found")
        return False
    
    print_success(f"AWS CLI: {stdout.strip()}")
    
    # Check credentials
    success, stdout, stderr = run_command("aws sts get-caller-identity")
    if not success:
        print_error("AWS credentials not configured")
        print_info("Run: aws configure")
        return False
    
    try:
        identity = json.loads(stdout)
        print_success(f"AWS Account: {identity.get('Account')}")
        print_success(f"AWS Region configured: {os.environ.get('AWS_DEFAULT_REGION', 'Not set')}")
        return True
    except:
        print_error("Could not parse AWS identity")
        return False

def check_docker() -> bool:
    """Check Docker availability"""
    print_info("Checking Docker...")
    
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print_error("Docker not found")
        return False
    
    print_success(f"Docker: {stdout.strip()}")
    
    # Check if Docker is running
    success, stdout, stderr = run_command("docker ps")
    if not success:
        print_error("Docker is not running")
        print_info("Please start Docker Desktop")
        return False
    
    print_success("Docker is running")
    return True

def check_python_dependencies() -> bool:
    """Check Python dependencies"""
    print_info("Checking Python dependencies...")
    
    required_packages = ['boto3', 'requests']
    missing_packages = []
    
    for package in required_packages:
        success, stdout, stderr = run_command(f"python -c \"import {package}\"")
        if success:
            print_success(f"Package {package}: Available")
        else:
            missing_packages.append(package)
            print_warning(f"Package {package}: Missing")
    
    if missing_packages:
        print_info(f"Install missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_terraform() -> bool:
    """Check Terraform availability"""
    print_info("Checking Terraform...")
    
    success, stdout, stderr = run_command("terraform version")
    if not success:
        print_error("Terraform not found")
        print_info("Install from: https://www.terraform.io/downloads")
        return False
    
    print_success("Terraform available")
    
    # Check if infra directory has .terraform
    if Path('infra/.terraform').exists():
        print_success("Terraform initialized")
    else:
        print_info("Terraform not initialized (will be done during deployment)")
    
    return True

def check_backend_completeness() -> bool:
    """Check backend application completeness"""
    print_info("Checking backend completeness...")
    
    # Check if main.py can be imported (syntax check)
    success, stdout, stderr = run_command("python -m py_compile backend/main.py")
    if not success:
        print_error("Backend main.py has syntax errors")
        return False
    
    print_success("Backend main.py syntax is valid")
    
    # Check requirements.txt
    if Path('backend/requirements.txt').exists():
        with open('backend/requirements.txt', 'r') as f:
            requirements = f.read()
            
        if 'fastapi' in requirements and 'uvicorn' in requirements:
            print_success("Backend requirements look good")
        else:
            print_warning("Backend requirements may be incomplete")
    
    return True

def check_frontend_completeness() -> bool:
    """Check frontend application completeness"""
    print_info("Checking frontend completeness...")
    
    # Check package.json
    if Path('frontend/package.json').exists():
        with open('frontend/package.json', 'r') as f:
            try:
                package_data = json.load(f)
                
                if 'next' in package_data.get('dependencies', {}):
                    print_success("Frontend package.json looks good")
                else:
                    print_warning("Frontend may be missing Next.js")
                    
                # Check build script
                if 'build' in package_data.get('scripts', {}):
                    print_success("Frontend build script exists")
                else:
                    print_warning("Frontend build script missing")
                    
            except json.JSONDecodeError:
                print_error("Frontend package.json is invalid")
                return False
    else:
        print_error("Frontend package.json not found")
        return False
    
    return True

def main():
    """Main validation function"""
    print_header()
    
    all_checks = []
    
    # File check
    missing_files = check_required_files()
    all_checks.append(len(missing_files) == 0)
    
    print()
    
    # Environment check
    all_checks.append(check_environment_setup())
    
    print()
    
    # AWS check
    all_checks.append(check_aws_setup())
    
    print()
    
    # Docker check
    all_checks.append(check_docker())
    
    print()
    
    # Python dependencies
    all_checks.append(check_python_dependencies())
    
    print()
    
    # Terraform check
    all_checks.append(check_terraform())
    
    print()
    
    # Backend check
    all_checks.append(check_backend_completeness())
    
    print()
    
    # Frontend check
    all_checks.append(check_frontend_completeness())
    
    print()
    print("=" * 50)
    
    if all(all_checks):
        print_success("🎉 ALL CHECKS PASSED - READY FOR DEPLOYMENT!")
        print()
        print_info("You can now run the go-live script:")
        print(f"   {Colors.CYAN}python scripts/go-live.py{Colors.END}")
        sys.exit(0)
    else:
        failed_checks = sum(1 for check in all_checks if not check)
        print_error(f"❌ {failed_checks} checks failed - FIX ISSUES BEFORE DEPLOYMENT")
        print()
        print_info("Fix the issues above, then re-run this validation script")
        sys.exit(1)

if __name__ == "__main__":
    main()
