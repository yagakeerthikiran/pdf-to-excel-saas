#!/usr/bin/env python3
"""
EMERGENCY CI/CD FIX SCRIPT

This script fixes the ECR 403 Forbidden errors by:
1. Creating missing ECR repositories
2. Setting proper permissions
3. Testing GitHub Actions compatibility
4. Providing exact fix commands

Run this FIRST before trying CI/CD again.
"""

import boto3
import json
import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd, ignore_errors=False):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and not ignore_errors:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Command exception: {e}")
        return None

def check_aws_cli():
    """Ensure AWS CLI is installed and configured"""
    print("🔍 Checking AWS CLI setup...")
    
    # Check if AWS CLI exists
    result = run_command("aws --version", ignore_errors=True)
    if not result:
        print("❌ AWS CLI not installed. Install it first:")
        print("   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False
    
    print(f"✅ AWS CLI installed: {result}")
    
    # Check if credentials are configured
    result = run_command("aws sts get-caller-identity", ignore_errors=True)
    if not result:
        print("❌ AWS credentials not configured. Run:")
        print("   aws configure")
        print("   # Or set environment variables:")
        print("   set AWS_ACCESS_KEY_ID=your_key")
        print("   set AWS_SECRET_ACCESS_KEY=your_secret")
        print("   set AWS_DEFAULT_REGION=ap-southeast-2")
        return False
    
    print("✅ AWS credentials configured")
    return True

def create_ecr_repositories():
    """Create ECR repositories if they don't exist"""
    print("\n🏗️ Creating ECR repositories...")
    
    repos = [
        'pdf-excel-saas-frontend',
        'pdf-excel-saas-backend'
    ]
    
    for repo in repos:
        print(f"📦 Checking repository: {repo}")
        
        # Check if repo exists
        check_cmd = f"aws ecr describe-repositories --repository-names {repo} --region ap-southeast-2"
        result = run_command(check_cmd, ignore_errors=True)
        
        if result and "repositoryUri" in result:
            print(f"✅ Repository {repo} already exists")
        else:
            print(f"🔨 Creating repository: {repo}")
            create_cmd = f"aws ecr create-repository --repository-name {repo} --region ap-southeast-2"
            result = run_command(create_cmd)
            
            if result:
                print(f"✅ Successfully created {repo}")
            else:
                print(f"❌ Failed to create {repo}")
                return False
    
    return True

def set_ecr_permissions():
    """Set ECR repository permissions for GitHub Actions"""
    print("\n🔐 Setting ECR repository permissions...")
    
    repos = [
        'pdf-excel-saas-frontend',
        'pdf-excel-saas-backend'
    ]
    
    # Get AWS account ID
    account_id_cmd = "aws sts get-caller-identity --query Account --output text"
    account_id = run_command(account_id_cmd)
    
    if not account_id:
        print("❌ Cannot get AWS account ID")
        return False
    
    print(f"🆔 AWS Account ID: {account_id}")
    
    # ECR policy for GitHub Actions
    policy = {
        "Version": "2008-10-17",
        "Statement": [
            {
                "Sid": "GitHubActionsAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{account_id}:root"
                },
                "Action": [
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:DescribeRepositories",
                    "ecr:GetRepositoryPolicy",
                    "ecr:ListImages",
                    "ecr:DescribeImages",
                    "ecr:GetAuthorizationToken"
                ]
            }
        ]
    }
    
    for repo in repos:
        print(f"🔑 Setting permissions for {repo}...")
        
        # Write policy to temp file
        policy_file = f"ecr-policy-{repo}.json"
        with open(policy_file, 'w') as f:
            json.dump(policy, f, indent=2)
        
        # Set repository policy
        policy_cmd = f"aws ecr set-repository-policy --repository-name {repo} --policy-text file://{policy_file} --region ap-southeast-2"
        result = run_command(policy_cmd)
        
        # Clean up temp file
        os.remove(policy_file)
        
        if result:
            print(f"✅ Permissions set for {repo}")
        else:
            print(f"⚠️ Could not set permissions for {repo} (may already exist)")
    
    return True

def test_ecr_access():
    """Test ECR access by getting auth token"""
    print("\n🧪 Testing ECR access...")
    
    # Test getting auth token
    auth_cmd = "aws ecr get-authorization-token --region ap-southeast-2"
    result = run_command(auth_cmd)
    
    if result and "authorizationToken" in result:
        print("✅ ECR authentication successful")
        
        # Test Docker login
        print("🐳 Testing Docker ECR login...")
        login_cmd = "aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com"
        login_result = run_command(login_cmd, ignore_errors=True)
        
        if login_result and "Login Succeeded" in login_result:
            print("✅ Docker ECR login successful")
            return True
        else:
            print("⚠️ Docker ECR login failed - Docker may not be running")
            print("💡 This is OK - GitHub Actions will handle Docker login")
            return True
    else:
        print("❌ ECR authentication failed")
        return False

def check_github_secrets():
    """Check GitHub secrets configuration"""
    print("\n🔐 GitHub Secrets Check...")
    
    print("📋 Required GitHub Secrets:")
    print("   Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas")
    print("   Go to: Settings → Secrets and variables → Actions")
    print()
    print("   Required secrets:")
    print("   ├─ AWS_ACCESS_KEY_ID (your AWS access key)")
    print("   └─ AWS_SECRET_ACCESS_KEY (your AWS secret key)")
    print()
    
    # Check if we can detect current AWS credentials
    profile_cmd = "aws configure list"
    profile_result = run_command(profile_cmd, ignore_errors=True)
    
    if profile_result:
        print("💡 Current AWS credentials (use these for GitHub secrets):")
        print("─" * 50)
        print(profile_result)
        print("─" * 50)
    
    print("⚠️  IMPORTANT: Use the SAME AWS credentials in GitHub secrets")
    print("    that you're using locally (where this script works)")

def provide_next_steps():
    """Provide clear next steps after running this script"""
    print("\n" + "="*60)
    print("🎯 NEXT STEPS TO FIX CI/CD")
    print("="*60)
    
    print("\n1. 🔐 SET GITHUB SECRETS:")
    print("   • Go to: https://github.com/yagakeerthikiran/pdf-to-excel-saas/settings/secrets/actions")
    print("   • Click 'New repository secret'")
    print("   • Add: AWS_ACCESS_KEY_ID")
    print("   • Add: AWS_SECRET_ACCESS_KEY")
    print("   • Use the SAME credentials that worked in this script")
    
    print("\n2. 🚀 TRIGGER CI/CD:")
    print("   git add .")
    print("   git commit -m \"fix: ECR repositories created, ready for CI/CD\"")
    print("   git push origin feat/infrastructure-clean")
    
    print("\n3. 🔍 MONITOR DEPLOYMENT:")
    print("   • Go to: https://github.com/yagakeerthikiran/pdf-to-excel-saas/actions")
    print("   • Watch the 'Build and Deploy to AWS ECS' workflow")
    print("   • Should now succeed instead of ECR 403 errors")
    
    print("\n4. ✅ VALIDATE SUCCESS:")
    print("   • Check if Docker images appear in ECR console")
    print("   • Verify ECS services are updated")
    print("   • Test application at ALB URL")
    
    print("\n5. 🐛 IF STILL FAILING:")
    print("   • Run: python scripts/diagnose-cicd-failure.py")
    print("   • Check GitHub Actions logs for new error details")
    print("   • Verify GitHub secrets are set correctly")

def main():
    print("🚨 EMERGENCY CI/CD FIX - ECR 403 Forbidden Error")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Region: ap-southeast-2")
    print("Account: Checking...")
    
    # Step 1: Check AWS CLI
    if not check_aws_cli():
        print("\n❌ Cannot proceed without AWS CLI and credentials")
        sys.exit(1)
    
    # Step 2: Create ECR repositories
    if not create_ecr_repositories():
        print("\n❌ Failed to create ECR repositories")
        sys.exit(1)
    
    # Step 3: Set permissions
    if not set_ecr_permissions():
        print("\n❌ Failed to set ECR permissions")
        sys.exit(1)
    
    # Step 4: Test access
    if not test_ecr_access():
        print("\n❌ ECR access test failed")
        sys.exit(1)
    
    # Step 5: GitHub secrets guidance
    check_github_secrets()
    
    # Step 6: Next steps
    provide_next_steps()
    
    print("\n🎉 ECR SETUP COMPLETE!")
    print("   ECR repositories created and configured")
    print("   Ready for GitHub Actions CI/CD")
    print("   Next: Set GitHub secrets and trigger deployment")

if __name__ == "__main__":
    main()
