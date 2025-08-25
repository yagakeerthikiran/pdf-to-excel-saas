#!/usr/bin/env python3
"""
NO-TIMEOUT DOCKER BUILD SCRIPT - LET IT RUN AS LONG AS NEEDED
Removes artificial timeouts that interrupt long Docker builds
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

def run_command_patient(cmd, description, cwd=None):
    """Run command with NO timeout - let it take as long as needed"""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"⏰ NO TIMEOUT - This may take a while, please be patient...")
    
    try:
        # Use UTF-8 encoding to avoid Windows cp1252 issues
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # NO TIMEOUT - let it run forever if needed
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            text=True,
            env=env,
            encoding='utf-8',
            errors='ignore'  # Ignore encoding errors
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            return True
        else:
            print(f"❌ FAILED: {description}")
            print(f"Return code: {result.returncode}")
            return False
            
    except KeyboardInterrupt:
        print(f"\n⚠️ CANCELLED: {description} interrupted by user")
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
    
    try:
        # Get login password
        result = subprocess.run([
            'aws', 'ecr', 'get-login-password', '--region', region
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            token = result.stdout.strip()
            
            # Login to Docker  
            print("🔐 Authenticating with ECR...")
            login_result = subprocess.run([
                'docker', 'login', '--username', 'AWS', '--password-stdin',
                f'{account_id}.dkr.ecr.{region}.amazonaws.com'
            ], input=token, text=True, timeout=60)
            
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

def build_and_push_patient(service_name, dockerfile_name, account_id, region):
    """Build and push with infinite patience"""
    print(f"\n{'='*60}")
    print(f"🐳 BUILDING {service_name.upper()}")
    print(f"{'='*60}")
    
    ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-{service_name}"
    local_tag = f"pdf-excel-{service_name}:latest"
    
    print(f"📍 Working Directory: {os.path.abspath(service_name)}")
    print(f"📄 Dockerfile: {dockerfile_name}")
    print(f"🏷️  Local Tag: {local_tag}")
    print(f"🏭 ECR URI: {ecr_uri}")
    
    # Step 1: Build image (NO TIMEOUT)
    print(f"\n🔨 Step 1: Building {service_name} Docker image...")
    print(f"⏰ This may take anywhere from 10 minutes to 4 hours depending on your system")
    print(f"☕ Go grab some coffee, this is going to take a while...")
    
    start_time = time.time()
    
    if not run_command_patient([
        'docker', 'build',
        '--progress=plain',  # Show detailed build progress
        '-f', dockerfile_name,
        '-t', local_tag,
        '.'
    ], f"Building {service_name} image (NO TIMEOUT)", cwd=service_name):
        print(f"❌ {service_name} build failed after {time.time() - start_time:.1f} seconds")
        return False
    
    build_duration = time.time() - start_time
    print(f"✅ {service_name} build completed in {build_duration/60:.1f} minutes")
    
    # Step 2: Tag for ECR
    print(f"\n🏷️  Step 2: Tagging {service_name} image for ECR...")
    if not run_command_patient([
        'docker', 'tag', local_tag, f"{ecr_uri}:latest"
    ], f"Tagging {service_name} image"):
        return False
    
    # Step 3: Push to ECR (NO TIMEOUT)
    print(f"\n📤 Step 3: Pushing {service_name} image to ECR...")
    print(f"⏰ Upload speed depends on your internet connection...")
    
    push_start = time.time()
    if not run_command_patient([
        'docker', 'push', f"{ecr_uri}:latest"
    ], f"Pushing {service_name} image to ECR (NO TIMEOUT)"):
        return False
    
    push_duration = time.time() - push_start
    total_duration = time.time() - start_time
    
    print(f"✅ {service_name} COMPLETE!")
    print(f"   Build Time: {build_duration/60:.1f} minutes")
    print(f"   Push Time: {push_duration/60:.1f} minutes")
    print(f"   Total Time: {total_duration/60:.1f} minutes")
    
    return True

def main():
    """Main patient build process"""
    print("⏰ PATIENT DOCKER BUILD - NO TIMEOUTS")
    print("=" * 60)
    print("🕰️  This script will wait as long as needed for Docker builds to complete")
    print("☕ Perfect time to grab coffee, lunch, or even take a nap!")
    print("⚠️  Press Ctrl+C if you want to cancel at any time")
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
        else:
            print("❌ Docker check failed")
            return False
    except:
        print("❌ Docker is not available - please start Docker Desktop")
        return False
    
    # Check Docker daemon
    try:
        result = subprocess.run(['docker', 'info'], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Docker daemon is running")
        else:
            print("❌ Docker daemon is not running - please start Docker Desktop")
            return False
    except:
        print("❌ Docker daemon check failed")
        return False
    
    # Check AWS CLI
    try:
        result = subprocess.run(['aws', '--version'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ AWS CLI: {result.stdout.strip()}")
        else:
            print("❌ AWS CLI check failed")
            return False
    except:
        print("❌ AWS CLI is not available")
        return False
    
    # Get AWS info
    account_id, region = get_aws_info()
    if not account_id:
        return False
    
    print(f"✅ AWS Account: {account_id}")
    print(f"✅ AWS Region: {region}")
    
    # ECR login
    if not ecr_login(account_id, region):
        return False
    
    # Copy simple Dockerfiles
    print("\n📁 Using simplified Dockerfiles...")
    try:
        import shutil
        
        # Frontend
        if Path("frontend/Dockerfile.simple").exists():
            shutil.copy2("frontend/Dockerfile.simple", "frontend/Dockerfile.prod")
            print("✅ Frontend: Dockerfile.simple → Dockerfile.prod")
        
        # Backend  
        if Path("backend/Dockerfile.simple").exists():
            shutil.copy2("backend/Dockerfile.simple", "backend/Dockerfile.prod")
            print("✅ Backend: Dockerfile.simple → Dockerfile.prod")
            
    except Exception as e:
        print(f"❌ Failed to copy Dockerfiles: {e}")
        return False
    
    # Build and push images with infinite patience
    overall_start = time.time()
    success = True
    
    print(f"\n🚀 Starting patient build process...")
    print(f"📅 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Frontend
    print(f"\n" + "="*60)
    print(f"1️⃣ FRONTEND BUILD")
    print(f"="*60)
    if not build_and_push_patient('frontend', 'Dockerfile.prod', account_id, region):
        success = False
        print("❌ Frontend build/push failed")
    
    # Backend
    print(f"\n" + "="*60) 
    print(f"2️⃣ BACKEND BUILD")
    print(f"="*60)
    if not build_and_push_patient('backend', 'Dockerfile.prod', account_id, region):
        success = False
        print("❌ Backend build/push failed")
    
    # Final summary
    overall_duration = time.time() - overall_start
    print(f"\n{'='*60}")
    print(f"🏁 PATIENT BUILD COMPLETE")
    print(f"{'='*60}")
    print(f"📅 Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Total time: {overall_duration/60:.1f} minutes ({overall_duration/3600:.1f} hours)")
    
    if success:
        print("🎉 ALL IMAGES BUILT AND PUSHED SUCCESSFULLY!")
        print(f"\n🚀 Next steps:")
        print(f"1. Go to AWS ECS Console")
        print(f"2. Find cluster: pdf-excel-saas-prod")
        print(f"3. Update services to use new images:")
        print(f"   Frontend: {account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-frontend:latest")
        print(f"   Backend: {account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-backend:latest")
        print(f"4. Wait for ECS deployment (5-10 minutes)")
        print(f"5. Test: http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com")
    else:
        print("❌ SOME BUILDS FAILED")
        print("   Check the error messages above")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Build cancelled by user")
        print("   You can restart anytime with: python scripts\\patient-docker-build.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)
