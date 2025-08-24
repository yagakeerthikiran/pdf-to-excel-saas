#!/usr/bin/env python3
"""
MANUAL DOCKER BUILD SCRIPT - WINDOWS COMPATIBLE
Builds and pushes Docker images manually with proper error handling
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

def run_command_safe(cmd, description, cwd=None, timeout=1200):
    """Run command with Windows encoding fixes"""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Use UTF-8 encoding to avoid Windows cp1252 issues
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            env=env,
            encoding='utf-8',
            errors='ignore'  # Ignore encoding errors
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            return True
        else:
            print(f"❌ FAILED: {description}")
            print(f"Error: {result.stderr[:1000]}...")  # Limit output
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {description} took longer than {timeout/60} minutes")
        return False
    except Exception as e:
        print(f"💥 ERROR: {description} - {str(e)}")
        return False

def get_aws_info():
    """Get AWS account and region info"""
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            account_id = info.get('Account', '')
            region = 'ap-southeast-2'
            return account_id, region
        else:
            print("❌ Failed to get AWS account info")
            return None, None
    except Exception as e:
        print(f"❌ AWS CLI error: {e}")
        return None, None

def ecr_login(account_id, region):
    """Login to ECR"""
    print(f"\n🔑 Logging into ECR...")
    
    # Get login token
    try:
        result = subprocess.run([
            'aws', 'ecr', 'get-login-password', '--region', region
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            token = result.stdout.strip()
            
            # Login to Docker
            login_result = subprocess.run([
                'docker', 'login', '--username', 'AWS', '--password-stdin',
                f'{account_id}.dkr.ecr.{region}.amazonaws.com'
            ], input=token, text=True, timeout=30)
            
            if login_result.returncode == 0:
                print("✅ ECR login successful")
                return True
            else:
                print("❌ ECR login failed")
                return False
        else:
            print("❌ Failed to get ECR login token")
            return False
    except Exception as e:
        print(f"❌ ECR login error: {e}")
        return False

def build_and_push_image(service_name, dockerfile_name, account_id, region):
    """Build and push a single Docker image"""
    print(f"\n🐳 Building {service_name}...")
    
    ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-{service_name}"
    local_tag = f"pdf-excel-{service_name}:latest"
    
    # Step 1: Build image
    if not run_command_safe([
        'docker', 'build', 
        '-f', dockerfile_name,
        '-t', local_tag,
        '.'
    ], f"Building {service_name} image", cwd=service_name, timeout=600):
        return False
    
    # Step 2: Tag for ECR
    if not run_command_safe([
        'docker', 'tag', local_tag, f"{ecr_uri}:latest"
    ], f"Tagging {service_name} image"):
        return False
    
    # Step 3: Push to ECR
    if not run_command_safe([
        'docker', 'push', f"{ecr_uri}:latest"
    ], f"Pushing {service_name} image to ECR", timeout=600):
        return False
    
    print(f"✅ {service_name} image successfully built and pushed!")
    return True

def main():
    """Main manual build process"""
    print("🛠️  MANUAL DOCKER BUILD - WINDOWS COMPATIBLE")
    print("=" * 60)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    # Check Docker
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        print("✅ Docker is available")
    except:
        print("❌ Docker is not available or not started")
        print("   Please start Docker Desktop and try again")
        return False
    
    # Check AWS CLI
    try:
        subprocess.run(['aws', '--version'], check=True, capture_output=True)
        print("✅ AWS CLI is available")
    except:
        print("❌ AWS CLI is not available")
        print("   Please install AWS CLI and configure credentials")
        return False
    
    # Get AWS info
    account_id, region = get_aws_info()
    if not account_id:
        print("❌ Failed to get AWS account information")
        return False
    
    print(f"✅ AWS Account: {account_id}")
    print(f"✅ AWS Region: {region}")
    
    # ECR login
    if not ecr_login(account_id, region):
        print("❌ ECR login failed")
        return False
    
    # Pull latest code
    print("\n📥 Pulling latest code...")
    run_command_safe(['git', 'pull', 'origin', 'feat/infrastructure-clean'], 
                    "Pulling latest changes")
    
    # Copy simple Dockerfiles
    print("\n📁 Using simplified Dockerfiles...")
    try:
        import shutil
        
        # Frontend
        if Path("frontend/Dockerfile.simple").exists():
            shutil.copy2("frontend/Dockerfile.simple", "frontend/Dockerfile.prod")
            print("✅ Frontend Dockerfile.simple → Dockerfile.prod")
        
        # Backend  
        if Path("backend/Dockerfile.simple").exists():
            shutil.copy2("backend/Dockerfile.simple", "backend/Dockerfile.prod")
            print("✅ Backend Dockerfile.simple → Dockerfile.prod")
            
    except Exception as e:
        print(f"❌ Failed to copy Dockerfiles: {e}")
        return False
    
    # Build and push images
    success = True
    
    # Frontend
    if not build_and_push_image('frontend', 'Dockerfile.prod', account_id, region):
        success = False
        print("❌ Frontend build/push failed")
    
    # Backend
    if not build_and_push_image('backend', 'Dockerfile.prod', account_id, region):
        success = False
        print("❌ Backend build/push failed")
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 ALL IMAGES BUILT AND PUSHED SUCCESSFULLY!")
        print(f"\n🚀 Next steps:")
        print(f"1. Go to AWS ECS Console")
        print(f"2. Find cluster: pdf-excel-saas-prod")
        print(f"3. Update services to use new images:")
        print(f"   - Frontend: {account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-frontend:latest")
        print(f"   - Backend: {account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-backend:latest")
        print(f"4. Wait for deployment")
        print(f"5. Test: http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com")
    else:
        print("❌ SOME IMAGES FAILED TO BUILD")
        print("   Check the errors above and try building individually")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)
