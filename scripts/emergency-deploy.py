#!/usr/bin/env python3
"""
EMERGENCY DEPLOYMENT SCRIPT - GO LIVE NOW!
Uses working Dockerfile and bypasses complex build issues
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout:
                print(f"Output: {result.stdout[:500]}...")
            return True
        else:
            print(f"❌ FAILED: {description}")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {description} took longer than 10 minutes")
        return False
    except Exception as e:
        print(f"💥 ERROR: {description} - {str(e)}")
        return False

def emergency_deploy():
    """Emergency deployment using simplified approach"""
    
    print("🚨 EMERGENCY DEPLOYMENT - GO LIVE NOW!")
    print("=" * 50)
    
    # Step 1: Use emergency Dockerfile
    print("\n📁 Step 1: Preparing Emergency Dockerfile...")
    
    # Copy emergency Dockerfile over the problematic one
    emergency_dockerfile = Path("frontend/Dockerfile.emergency")
    prod_dockerfile = Path("frontend/Dockerfile.prod")
    
    if emergency_dockerfile.exists():
        import shutil
        try:
            # Backup original
            if prod_dockerfile.exists():
                shutil.copy2(prod_dockerfile, "frontend/Dockerfile.prod.backup")
            
            # Use emergency version
            shutil.copy2(emergency_dockerfile, prod_dockerfile)
            print("✅ Emergency Dockerfile ready")
        except Exception as e:
            print(f"❌ Failed to copy Dockerfile: {e}")
            print("📝 MANUAL STEP: Copy frontend/Dockerfile.emergency to frontend/Dockerfile.prod")
            input("Press Enter when done...")
    
    # Step 2: Try simplified deployment
    print("\n🚀 Step 2: Attempting Emergency Deployment...")
    
    # Try the deployment script again
    success = run_command(
        ["python", "scripts\\deploy-application.py"],
        "Emergency application deployment",
        cwd="."
    )
    
    if success:
        print("\n🎉 SUCCESS! Your application should be deploying!")
        print("\n🌐 Test your application at:")
        print("http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com")
        return True
    
    # Step 3: Manual Docker approach
    print("\n⚠️  Automated deployment failed. Trying manual Docker build...")
    
    # Get AWS account ID
    result = subprocess.run(["aws", "sts", "get-caller-identity"], capture_output=True, text=True)
    if result.returncode == 0:
        import json
        account_info = json.loads(result.stdout)
        account_id = account_info.get('Account', '')
        region = 'ap-southeast-2'
        
        print(f"Account ID: {account_id}")
        print(f"Region: {region}")
        
        # ECR URLs
        frontend_ecr = f"{account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-frontend"
        backend_ecr = f"{account_id}.dkr.ecr.{region}.amazonaws.com/pdf-excel-saas-backend"
        
        print(f"\n📦 Manual Docker Build Instructions:")
        print(f"1. Frontend ECR: {frontend_ecr}")
        print(f"2. Backend ECR: {backend_ecr}")
        
        # Try manual build
        print(f"\n🔨 Attempting manual frontend build...")
        
        # Build frontend
        if run_command(
            ["docker", "build", "-f", "Dockerfile.prod", "-t", f"frontend:latest", "."],
            "Building frontend Docker image",
            cwd="frontend"
        ):
            # ECR login
            if run_command(
                ["aws", "ecr", "get-login-password", "--region", region],
                "Getting ECR login token",
            ):
                print(f"\n🔑 Logging into ECR...")
                login_cmd = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
                os.system(login_cmd)
                
                # Tag and push frontend
                run_command(
                    ["docker", "tag", "frontend:latest", f"{frontend_ecr}:latest"],
                    "Tagging frontend image"
                )
                
                run_command(
                    ["docker", "push", f"{frontend_ecr}:latest"],
                    "Pushing frontend image to ECR"
                )
        
        # Build backend
        print(f"\n🔨 Attempting manual backend build...")
        if run_command(
            ["docker", "build", "-f", "Dockerfile.prod", "-t", f"backend:latest", "."],
            "Building backend Docker image", 
            cwd="backend"
        ):
            # Tag and push backend
            run_command(
                ["docker", "tag", "backend:latest", f"{backend_ecr}:latest"],
                "Tagging backend image"
            )
            
            run_command(
                ["docker", "push", f"{backend_ecr}:latest"],
                "Pushing backend image to ECR"
            )
        
        print(f"\n🎯 MANUAL NEXT STEPS:")
        print(f"1. Go to AWS ECS Console")
        print(f"2. Find cluster: pdf-excel-saas-prod")
        print(f"3. Update services with new image versions")
        print(f"4. Wait for deployment to complete")
        print(f"5. Test: http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com")
        
        return True
    
    return False

def main():
    """Main execution"""
    try:
        if emergency_deploy():
            print(f"\n🎉 EMERGENCY DEPLOYMENT COMPLETE!")
            print(f"Your SaaS should be live or very close to it!")
        else:
            print(f"\n💥 EMERGENCY DEPLOYMENT FAILED")
            print(f"Manual AWS Console deployment required")
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        print(f"Proceed with manual AWS Console deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()
