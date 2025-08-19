#!/usr/bin/env python3
"""
Simple Infrastructure Deployment Script - Technical Debt Reduction
- Single responsibility: Deploy infrastructure
- Minimal complexity: Essential features only
- Clear error handling: Simple and direct
- No file modification: Never touches Terraform files

Troubleshooting Notes
---------------------
Issue: "ResourceInUse" errors when deleting ELB target groups.
Solution: The target group is still attached to an ALB listener. Detach or
remove the listener/ALB before re-running the deployment.

Issue: "InvalidParameterValue" for RDS subnet groups.
Solution: Ensure all subnets defined for the DB subnet group belong to the same
VPC.

Issue: "InvalidConfigurationRequest" about security groups.
Solution: One or more security group IDs are incorrect or deleted. Verify the
IDs and that they exist in the selected AWS region.
"""

import subprocess
import json
import sys
from pathlib import Path

AWS_REGION = "ap-southeast-2"
APP_NAME = "pdf-excel-saas"
ENVIRONMENT = "prod"

def run_command(cmd, cwd=None):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_aws_credentials():
    """Verify AWS credentials"""
    success, stdout, stderr = run_command(f'aws sts get-caller-identity --region {AWS_REGION}')
    
    if success:
        try:
            account = json.loads(stdout)['Account']
            print(f"✅ AWS Account: {account}")
            return True
        except:
            pass
    
    print("❌ AWS credentials not configured")
    print("Run: aws configure")
    return False

def deploy_infrastructure():
    """Simple infrastructure deployment"""
    print("🚀 Deploying infrastructure...")
    
    # Initialize Terraform
    print("Initializing Terraform...")
    success, _, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print(f"❌ Init failed: {stderr}")
        return False
    
    # Plan deployment
    print("Planning deployment...")
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, _, stderr = run_command(plan_cmd, cwd='infra')
    if not success:
        print(f"❌ Plan failed: {stderr}")
        return False
    
    # Confirm deployment
    confirm = input("Apply changes? (y/N): ")
    if confirm.lower() != 'y':
        print("Deployment cancelled")
        return False
    
    # Apply changes
    print("Applying changes...")
    apply_cmd = (
        f'terraform apply -auto-approve -var="aws_region={AWS_REGION}" '
        f'-var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    )
    success, _, stderr = run_command(apply_cmd, cwd="infra")
    
    if success:
        print("✅ Infrastructure deployed successfully")
        return True
    else:
        print(f"❌ Apply failed: {stderr}")

        # Provide guidance for common failures
        if "ResourceInUse" in stderr:
            print("👉 Detach the target group from any ALB listeners before retrying.")
        if "InvalidParameterValue" in stderr and "DBSubnetGroup" in stderr:
            print("👉 RDS subnets must all belong to the same VPC.")
        if "InvalidConfigurationRequest" in stderr and "security groups" in stderr:
            print("👉 Verify that the referenced security group IDs exist in this region.")

        return False

def main():
    """Main deployment function"""
    print(f"PDF to Excel SaaS - Infrastructure Deployment")
    print(f"Region: {AWS_REGION} | Environment: {ENVIRONMENT}")
    
    if not check_aws_credentials():
        sys.exit(1)
    
    if not Path('infra/main.tf').exists():
        print("❌ Terraform configuration not found")
        sys.exit(1)
    
    if deploy_infrastructure():
        print("\n🎉 Deployment completed!")
        print("Next steps:")
        print("1. Build and push Docker images")
        print("2. Deploy application to ECS")
    else:
        print("\n❌ Deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
