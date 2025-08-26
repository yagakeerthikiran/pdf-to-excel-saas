#!/usr/bin/env python3
"""
CI/CD Pipeline Failure Diagnostics

This script diagnoses the root cause of GitHub Actions failures,
specifically the ECR 403 Forbidden push errors.

Run this to identify and fix deployment pipeline issues.
"""

import boto3
import json
import sys
import os
from datetime import datetime

def print_header(text):
    print(f"\n{'='*60}")
    print(f"🔍 {text}")
    print(f"{'='*60}")

def print_status(status, message):
    emoji = "✅" if status else "❌"
    print(f"{emoji} {message}")

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    print_header("AWS CREDENTIALS CHECK")
    
    try:
        # Try to get caller identity
        sts = boto3.client('sts', region_name='ap-southeast-2')
        identity = sts.get_caller_identity()
        
        account_id = identity['Account']
        user_arn = identity['Arn']
        
        print_status(True, f"AWS credentials are valid")
        print(f"   Account ID: {account_id}")
        print(f"   User/Role: {user_arn}")
        
        return True, account_id
        
    except Exception as e:
        print_status(False, f"AWS credentials invalid or missing: {e}")
        print("\nℹ️ Make sure to set AWS credentials:")
        print("   export AWS_ACCESS_KEY_ID=your_key")
        print("   export AWS_SECRET_ACCESS_KEY=your_secret")
        print("   export AWS_DEFAULT_REGION=ap-southeast-2")
        return False, None

def check_ecr_repositories(account_id):
    """Check if ECR repositories exist"""
    print_header("ECR REPOSITORIES CHECK")
    
    if not account_id:
        print_status(False, "Cannot check ECR - AWS credentials invalid")
        return False
    
    try:
        ecr = boto3.client('ecr', region_name='ap-southeast-2')
        
        expected_repos = [
            'pdf-excel-saas-frontend',
            'pdf-excel-saas-backend'
        ]
        
        # List all repositories
        response = ecr.describe_repositories()
        existing_repos = [repo['repositoryName'] for repo in response['repositories']]
        
        all_exist = True
        for repo in expected_repos:
            if repo in existing_repos:
                print_status(True, f"ECR repository '{repo}' exists")
                
                # Check repository permissions
                try:
                    policy_response = ecr.get_repository_policy(repositoryName=repo)
                    print(f"   ✅ Repository policy configured")
                except ecr.exceptions.RepositoryPolicyNotFoundException:
                    print(f"   ⚠️ No repository policy set")
                except Exception as e:
                    print(f"   ❌ Cannot check repository policy: {e}")
                    
            else:
                print_status(False, f"ECR repository '{repo}' does not exist")
                all_exist = False
        
        if not all_exist:
            print("\n💡 Create missing ECR repositories:")
            for repo in expected_repos:
                if repo not in existing_repos:
                    print(f"   aws ecr create-repository --repository-name {repo} --region ap-southeast-2")
        
        return all_exist
        
    except Exception as e:
        print_status(False, f"Cannot access ECR: {e}")
        return False

def check_ecr_permissions(account_id):
    """Check ECR push/pull permissions"""
    print_header("ECR PERMISSIONS CHECK")
    
    if not account_id:
        print_status(False, "Cannot check ECR permissions - AWS credentials invalid")
        return False
    
    try:
        ecr = boto3.client('ecr', region_name='ap-southeast-2')
        
        # Try to get authorization token (required for docker push)
        auth_response = ecr.get_authorization_token()
        print_status(True, "Can get ECR authorization token")
        
        # Check if we can list repositories
        repos_response = ecr.describe_repositories()
        print_status(True, f"Can list ECR repositories ({len(repos_response['repositories'])} found)")
        
        return True
        
    except Exception as e:
        print_status(False, f"ECR permissions issue: {e}")
        print("\n💡 Required ECR permissions:")
        print("   - ecr:GetAuthorizationToken")
        print("   - ecr:BatchCheckLayerAvailability")
        print("   - ecr:GetDownloadUrlForLayer")
        print("   - ecr:GetRepositoryPolicy")
        print("   - ecr:DescribeRepositories")
        print("   - ecr:ListImages")
        print("   - ecr:DescribeImages")
        print("   - ecr:BatchGetImage")
        print("   - ecr:InitiateLayerUpload")
        print("   - ecr:UploadLayerPart")
        print("   - ecr:CompleteLayerUpload")
        print("   - ecr:PutImage")
        return False

def check_ecs_infrastructure():
    """Check if ECS cluster and services exist"""
    print_header("ECS INFRASTRUCTURE CHECK")
    
    try:
        ecs = boto3.client('ecs', region_name='ap-southeast-2')
        
        cluster_name = 'pdf-excel-saas-prod'
        service_names = [
            'pdf-excel-saas-prod-frontend',
            'pdf-excel-saas-prod-backend'
        ]
        
        # Check cluster
        cluster_response = ecs.describe_clusters(clusters=[cluster_name])
        if cluster_response['clusters'] and cluster_response['clusters'][0]['status'] == 'ACTIVE':
            print_status(True, f"ECS cluster '{cluster_name}' is active")
            
            # Check services
            service_response = ecs.describe_services(
                cluster=cluster_name,
                services=service_names
            )
            
            for service in service_response['services']:
                service_name = service['serviceName']
                status = service['status']
                desired = service['desiredCount']
                running = service['runningCount']
                
                if status == 'ACTIVE':
                    print_status(True, f"ECS service '{service_name}' is active ({running}/{desired} running)")
                else:
                    print_status(False, f"ECS service '{service_name}' status: {status}")
            
            return True
        else:
            print_status(False, f"ECS cluster '{cluster_name}' does not exist or is not active")
            return False
            
    except Exception as e:
        print_status(False, f"Cannot access ECS: {e}")
        return False

def analyze_github_actions():
    """Analyze GitHub Actions configuration"""
    print_header("GITHUB ACTIONS ANALYSIS")
    
    workflow_file = ".github/workflows/build-and-deploy.yml"
    if os.path.exists(workflow_file):
        print_status(True, f"GitHub Actions workflow file exists")
        
        # Check for required secrets
        required_secrets = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY'
        ]
        
        print("\n🔐 Required GitHub Secrets:")
        for secret in required_secrets:
            env_value = os.environ.get(secret)
            if env_value:
                print_status(True, f"{secret} is set in environment")
            else:
                print_status(False, f"{secret} is NOT set in environment")
        
        print("\n💡 To set GitHub Secrets:")
        print("   1. Go to GitHub repository → Settings → Secrets and variables → Actions")
        print("   2. Add the following secrets:")
        for secret in required_secrets:
            print(f"      - {secret}")
            
        return True
    else:
        print_status(False, f"GitHub Actions workflow file not found")
        return False

def provide_solution():
    """Provide step-by-step solution"""
    print_header("SOLUTION STEPS")
    
    print("🎯 To fix the CI/CD pipeline:")
    print()
    print("1. **Deploy Infrastructure First:**")
    print("   python scripts/deploy-infrastructure.py")
    print()
    print("2. **Set GitHub Secrets:**")
    print("   - Go to: https://github.com/yagakeerthikiran/pdf-to-excel-saas/settings/secrets/actions")
    print("   - Add: AWS_ACCESS_KEY_ID")
    print("   - Add: AWS_SECRET_ACCESS_KEY")
    print()
    print("3. **Test ECR Access:**")
    print("   aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com")
    print()
    print("4. **Re-run GitHub Actions:**")
    print("   git push origin feat/infrastructure-clean")
    print()
    print("5. **Manual Docker Test (optional):**")
    print("   python scripts/manual-docker-build.py")

def main():
    print("🔍 PDF-to-Excel SaaS CI/CD Diagnostics")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    print(f"   Region: ap-southeast-2")
    
    # Run all checks
    aws_valid, account_id = check_aws_credentials()
    
    if aws_valid:
        ecr_repos_exist = check_ecr_repositories(account_id)
        ecr_perms_ok = check_ecr_permissions(account_id)
        ecs_ok = check_ecs_infrastructure()
        github_ok = analyze_github_actions()
        
        print_header("SUMMARY")
        
        if all([aws_valid, ecr_repos_exist, ecr_perms_ok, github_ok]):
            print("🎉 All checks passed - CI/CD should work!")
        else:
            issues = []
            if not ecr_repos_exist:
                issues.append("ECR repositories missing")
            if not ecr_perms_ok:
                issues.append("ECR permissions insufficient")
            if not ecs_ok:
                issues.append("ECS infrastructure missing")
            if not github_ok:
                issues.append("GitHub Actions config issues")
            
            print(f"❌ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   • {issue}")
    
    provide_solution()

if __name__ == "__main__":
    main()
