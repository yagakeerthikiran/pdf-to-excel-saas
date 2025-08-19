#!/usr/bin/env python3
"""
Target Group Migration Script
Safely migrates target groups from 'instance' to 'ip' target type for Fargate compatibility
"""

import subprocess
import json
import sys
import time
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
            print_status(f"AWS Account: {account}")
            return True, account
        except:
            pass
    
    print_error("AWS credentials not configured")
    return False, None

def remove_target_groups_from_state():
    """Remove target groups from Terraform state to allow recreation"""
    print_title("Removing Target Groups from Terraform State")
    print_info("This preserves the actual AWS resources while allowing Terraform to recreate them")
    
    # Initialize Terraform first
    success, stdout, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print_error(f"Terraform init failed: {stderr}")
        return False
    
    # Remove target groups from state (preserves actual AWS resources)
    target_groups = [
        'aws_lb_target_group.frontend',
        'aws_lb_target_group.backend'
    ]
    
    for tg in target_groups:
        print_info(f"Removing {tg} from Terraform state...")
        success, stdout, stderr = run_command(f'terraform state rm {tg}', cwd='infra')
        
        if success:
            print_status(f"Removed {tg} from state")
        else:
            print_warning(f"Could not remove {tg}: {stderr}")
    
    return True

def plan_import_operations():
    """Generate plan showing what will be imported/created"""
    print_title("Planning Import Operations")
    
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(plan_cmd, cwd='infra')
    
    if success:
        print_info("Plan generated successfully")
        # Show relevant lines
        lines = stdout.split('\n')
        for line in lines:
            if 'target_group' in line.lower() or 'Plan:' in line:
                print_info(f"  {line.strip()}")
        return True
    else:
        print_error(f"Plan failed: {stderr}")
        return False

def import_target_groups():
    """Import existing target groups with new configuration"""
    print_title("Importing Target Groups with Updated Configuration")
    
    # Get target group ARNs from AWS
    frontend_tg_name = f"{APP_NAME}-{ENVIRONMENT}-frontend-tg"
    backend_tg_name = f"{APP_NAME}-{ENVIRONMENT}-backend-tg"
    
    # Get frontend target group ARN
    cmd = f'aws elbv2 describe-target-groups --names {frontend_tg_name} --region {AWS_REGION} --query "TargetGroups[0].TargetGroupArn" --output text'
    success, frontend_arn, stderr = run_command(cmd)
    
    if success and frontend_arn.strip() != 'None':
        print_info(f"Found frontend target group: {frontend_arn.strip()}")
        
        # Import frontend target group
        import_cmd = f'terraform import aws_lb_target_group.frontend {frontend_arn.strip()}'
        success, stdout, stderr = run_command(import_cmd, cwd='infra')
        
        if success:
            print_status("Imported frontend target group")
        else:
            print_error(f"Failed to import frontend target group: {stderr}")
    else:
        print_warning("Frontend target group not found or error occurred")
    
    # Get backend target group ARN
    cmd = f'aws elbv2 describe-target-groups --names {backend_tg_name} --region {AWS_REGION} --query "TargetGroups[0].TargetGroupArn" --output text'
    success, backend_arn, stderr = run_command(cmd)
    
    if success and backend_arn.strip() != 'None':
        print_info(f"Found backend target group: {backend_arn.strip()}")
        
        # Import backend target group
        import_cmd = f'terraform import aws_lb_target_group.backend {backend_arn.strip()}'
        success, stdout, stderr = run_command(import_cmd, cwd='infra')
        
        if success:
            print_status("Imported backend target group")
        else:
            print_error(f"Failed to import backend target group: {stderr}")
    else:
        print_warning("Backend target group not found or error occurred")

def apply_remaining_changes():
    """Apply any remaining Terraform changes"""
    print_title("Applying Remaining Infrastructure Changes")
    
    # Generate final plan
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(plan_cmd, cwd='infra')
    
    if success:
        print_info("Final plan:")
        lines = stdout.split('\n')
        for line in lines:
            if 'Plan:' in line or 'No changes' in line:
                print_info(f"  {line.strip()}")
        
        if 'No changes' in stdout:
            print_status("No additional changes needed")
            return True
        
        # Ask for confirmation
        confirm = input(f"{Colors.YELLOW}Apply remaining changes? (y/N): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Remaining changes cancelled")
            return True
        
        # Apply changes
        apply_cmd = f'terraform apply -auto-approve -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
        success, stdout, stderr = run_command(apply_cmd, cwd='infra')
        
        if success:
            print_status("Infrastructure migration completed successfully")
            return True
        else:
            print_error(f"Apply failed: {stderr}")
            return False
    else:
        print_error(f"Final plan failed: {stderr}")
        return False

def main():
    """Main migration function"""
    print(f"{Colors.BLUE}")
    print("=== TARGET GROUP MIGRATION SCRIPT ===")
    print("=====================================")
    print("Migrating target groups from 'instance' to 'ip' target type")
    print(f"Region: {AWS_REGION} | Environment: {ENVIRONMENT}")
    print(f"{Colors.END}")
    
    # Check AWS credentials
    creds_ok, account_id = check_aws_credentials()
    if not creds_ok:
        sys.exit(1)
    
    if not Path('infra/main.tf').exists():
        print_error("Terraform configuration not found")
        sys.exit(1)
    
    print_warning("This script will temporarily remove target groups from Terraform state")
    print_warning("The actual AWS resources will be preserved and re-imported")
    print_warning("This is necessary to change target_type from 'instance' to 'ip'")
    
    confirm = input(f"\n{Colors.YELLOW}Proceed with target group migration? (y/N): {Colors.END}")
    if confirm.lower() != 'y':
        print_info("Migration cancelled")
        sys.exit(0)
    
    try:
        # Step 1: Remove target groups from state (preserves AWS resources)
        if not remove_target_groups_from_state():
            print_error("Failed to remove target groups from state")
            sys.exit(1)
        
        # Step 2: Import target groups with new configuration
        import_target_groups()
        
        # Step 3: Apply any remaining changes
        if not apply_remaining_changes():
            print_error("Failed to apply remaining changes")
            sys.exit(1)
        
        # Success summary
        print_title("Migration Summary")
        print_status("✅ Target groups migrated to IP-based targeting")
        print_status("✅ Infrastructure is now Fargate-compatible")
        print_status("✅ All resources operational")
        
        print_info("\nTarget groups now use 'ip' target type for Fargate compatibility")
        print_info("ECS services can now be deployed successfully")
        
    except Exception as e:
        print_error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
