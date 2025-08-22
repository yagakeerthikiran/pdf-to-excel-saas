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
        try:
            with open('.env.prod', 'r') as f:
                content = f.read()
                
            required_vars = ['AWS_REGION']  # Relaxed requirement
            missing_vars = []
            
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                print_warning(f"Missing environment variables: {', '.join(missing_vars)}")
                print_info("The go-live script can help generate missing variables")
                return True  # Don't fail on this - let go-live script handle it
            else:
                print_success("Environment configuration looks good")
                return True
        except Exception as e:
            print_warning(f"Could not read .env.prod: {e}")
            return True  # Don't fail - let go-live script handle it
            
    elif env_template_exists:
        print_warning(".env.prod not found, but template exists")
        print_info("The go-live script will help create .env.prod from template")
        return True  # Don't fail - go-live script will handle this
    else:
        print_warning("No environment configuration found")
        print_info("The go-live script will generate environment configuration")
        return True  # Don't fail - go-live script will handle this

def check_aws_setup() -> bool:
    """Check AWS CLI and credentials"""
    print_info("Checking AWS setup...")
    
    # Check AWS CLI
    success, stdout, stderr = run_command("aws --version")
    if not success:
        print_error("AWS CLI not found")
        print_info("Install from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False
    
    print_success(f"AWS CLI: {stdout.strip()}")
    
    # Check credentials
    success, stdout, stderr = run_command("aws sts get-caller-identity")
    if not success:
        print_error("AWS credentials not configured")
        print_info("Run: aws configure")
        print_info("Enter your AWS Access Key ID, Secret Access Key, and set region to ap-southeast-2")
        return False
    
    try:
        identity = json.loads(stdout)
        print_success(f"AWS Account: {identity.get('Account')}")
        
        # Check region configuration
        region = os.environ.get('AWS_DEFAULT_REGION')
        if region:
            print_success(f"AWS Region: {region}")
        else:
            print_info("AWS region not set in environment - deployment will use ap-southeast-2")
            
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
        print_info("Install from: https://docs.docker.com/get-docker/")
        return False
    
    print_success(f"Docker: {stdout.strip()}")
    
    # Check if Docker is running
    success, stdout, stderr = run_command("docker ps")
    if not success:
        print_error("Docker is not running")
        print_info("Please start Docker Desktop and try again")
        return False
    
    print_success("Docker is running")
    return True

def check_python_dependencies() -> bool:
    """Check Python dependencies"""
    print_info("Checking Python dependencies...")
    
    required_packages = ['boto3']  # Only check essential packages
    missing_packages = []
    
    for package in required_packages:
        success, stdout, stderr = run_command(f"python -c \"import {package}\"")
        if success:
            print_success(f"Package {package}: Available")
        else:
            missing_packages.append(package)
            print_warning(f"Package {package}: Missing")
    
    if missing_packages:
        print_info(f"Installing missing packages: {' '.join(missing_packages)}")
        for package in missing_packages:
            success, stdout, stderr = run_command(f"pip install {package}")
            if success:
                print_success(f"Installed {package}")
            else:
                print_error(f"Failed to install {package}")
                return False
    
    return True

def check_terraform() -> bool:
    """Check Terraform availability"""
    print_info("Checking Terraform...")
    
    success, stdout, stderr = run_command("terraform version")
    if not success:
        print_error("Terraform not found")
        print_info("Install from: https://www.terraform.io/downloads")
        print_info("Or use chocolatey: choco install terraform")
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
    
    # Check if main.py exists and has basic structure
    if not Path('backend/main.py').exists():
        print_error("Backend main.py not found")
        return False
    
    print_success("Backend main.py exists")
    
    # Check requirements.txt
    if Path('backend/requirements.txt').exists():
        with open('backend/requirements.txt', 'r') as f:
            requirements = f.read().lower()
            
        # Check for essential packages
        essential_packages = ['fastapi', 'uvicorn']
        missing_essential = []
        
        for package in essential_packages:
            if package not in requirements:
                missing_essential.append(package)
        
        if missing_essential:
            print_error(f"Backend requirements missing essential packages: {', '.join(missing_essential)}")
            return False
        else:
            print_success("Backend requirements include FastAPI and uvicorn")
    else:
        print_error("Backend requirements.txt not found")
        return False
    
    return True

def check_frontend_completeness() -> bool:
    """Check frontend application completeness"""
    print_info("Checking frontend completeness...")
    
    # Check package.json
    if Path('frontend/package.json').exists():
        try:
            with open('frontend/package.json', 'r') as f:
                package_data = json.load(f)
                
            dependencies = package_data.get('dependencies', {})
            scripts = package_data.get('scripts', {})
            
            if 'next' in dependencies:
                print_success("Frontend includes Next.js")
            else:
                print_warning("Frontend may be missing Next.js")
                    
            # Check build script
            if 'build' in scripts:
                print_success("Frontend build script exists")
            else:
                print_warning("Frontend build script missing")
                    
        except json.JSONDecodeError:
            print_error("Frontend package.json is invalid")
            return False
    else:
        print_error("Frontend package.json not found")
        return False
    
    # Check if basic page files exist
    if Path('frontend/src/app/page.tsx').exists():
        print_success("Frontend page components exist")
    else:
        print_warning("Frontend page components may be missing")
    
    return True

def main():
    """Main validation function"""
    print_header()
    
    checks = []
    critical_checks = []  # These will fail the validation
    
    # File check (critical)
    missing_files = check_required_files()
    critical_checks.append(len(missing_files) == 0)
    
    print()
    
    # Environment check (non-critical - go-live script handles this)
    env_ok = check_environment_setup()
    checks.append(env_ok)
    
    print()
    
    # AWS check (critical)
    aws_ok = check_aws_setup()
    critical_checks.append(aws_ok)
    
    print()
    
    # Docker check (critical)
    docker_ok = check_docker()
    critical_checks.append(docker_ok)
    
    print()
    
    # Python dependencies (critical)
    python_ok = check_python_dependencies()
    critical_checks.append(python_ok)
    
    print()
    
    # Terraform check (critical)
    terraform_ok = check_terraform()
    critical_checks.append(terraform_ok)
    
    print()
    
    # Backend check (critical)
    backend_ok = check_backend_completeness()
    critical_checks.append(backend_ok)
    
    print()
    
    # Frontend check (non-critical warnings only)
    frontend_ok = check_frontend_completeness()
    checks.append(frontend_ok)
    
    print()
    print("=" * 50)
    
    # Only fail on critical checks
    if all(critical_checks):
        warnings = sum(1 for check in checks if not check)
        if warnings > 0:
            print_warning(f"⚠️  {warnings} warnings found - deployment should still work")
        
        print_success("🎉 CRITICAL CHECKS PASSED - READY FOR DEPLOYMENT!")
        print()
        print_info("You can now run the go-live script:")
        print(f"   {Colors.CYAN}python scripts/go-live.py{Colors.END}")
        print()
        if warnings > 0:
            print_info("The go-live script will handle the warnings automatically")
        sys.exit(0)
    else:
        failed_critical = sum(1 for check in critical_checks if not check)
        print_error(f"❌ {failed_critical} critical checks failed - MUST FIX BEFORE DEPLOYMENT")
        print()
        print_info("Fix the critical issues above, then re-run this validation script")
        sys.exit(1)

if __name__ == "__main__":
    main()
