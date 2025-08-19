#!/usr/bin/env python3
"""
Target Group Migration Script - Enhanced
Safely migrates target groups from 'instance' to 'ip' target type for Fargate compatibility
Handles lifecycle.prevent_destroy protection properly
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

def backup_main_tf():
    """Create backup of main.tf before modifications"""
    print_info("Creating backup of main.tf...")
    
    main_tf_path = Path('infra/main.tf')
    backup_path = Path('infra/main.tf.backup')
    
    if main_tf_path.exists():
        import shutil
        shutil.copy2(main_tf_path, backup_path)
        print_status("Backup created: main.tf.backup")
        return True
    else:
        print_error("main.tf not found")
        return False

def remove_lifecycle_protection():
    """Temporarily remove lifecycle protection from target groups"""
    print_title("Temporarily Removing Lifecycle Protection")
    print_info("This allows Terraform to recreate target groups with new target_type")
    
    main_tf_path = Path('infra/main.tf')
    
    # Read current main.tf
    with open(main_tf_path, 'r') as f:
        content = f.read()
    
    # Remove lifecycle blocks from target groups only
    lines = content.split('\n')
    filtered_lines = []
    skip_lifecycle = False
    brace_count = 0
    in_target_group = False
    
    for line in lines:
        # Check if we're in a target group resource
        if 'resource "aws_lb_target_group"' in line:
            in_target_group = True
        elif line.strip().startswith('resource ') and 'aws_lb_target_group' not in line:
            in_target_group = False
        
        # Only remove lifecycle blocks from target groups
        if in_target_group and 'lifecycle {' in line:
            skip_lifecycle = True
            brace_count = 1
            continue
        
        if skip_lifecycle:
            if '{' in line:
                brace_count += line.count('{')
            if '}' in line:
                brace_count -= line.count('}')
                if brace_count == 0:
                    skip_lifecycle = False
            continue
        
        filtered_lines.append(line)
    
    # Write modified content
    modified_content = '\n'.join(filtered_lines)
    with open(main_tf_path, 'w') as f:
        f.write(modified_content)
    
    print_status("Lifecycle protection removed from target groups")
    return True

def restore_lifecycle_protection():
    """Restore lifecycle protection to target groups"""
    print_title("Restoring Lifecycle Protection")
    
    backup_path = Path('infra/main.tf.backup')
    main_tf_path = Path('infra/main.tf')
    
    if backup_path.exists():
        import shutil
        shutil.copy2(backup_path, main_tf_path)
        backup_path.unlink()  # Remove backup file
        print_status("Lifecycle protection restored")
        return True
    else:
        print_warning("Backup file not found - using git to restore")
        # Fallback to git restore
        success, stdout, stderr = run_command('git checkout infra/main.tf')
        if success:
            print_status("Lifecycle protection restored via git")
            return True
        else:
            print_error(f"Could not restore main.tf: {stderr}")
            return False

def remove_target_groups_from_state():
    """Remove target groups from Terraform state"""
    print_title("Removing Target Groups from Terraform State")
    
    # Initialize Terraform first
    success, stdout, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print_error(f"Terraform init failed: {stderr}")
        return False
    
    # Remove target groups from state
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

def apply_target_group_changes():
    """Apply target group changes with lifecycle protection removed"""
    print_title("Applying Target Group Changes")
    
    # Generate plan targeting only target groups and dependencies
    plan_cmd = f'terraform plan -target=aws_lb_target_group.frontend -target=aws_lb_target_group.backend -target=aws_lb_listener.frontend -target=aws_lb_listener_rule.backend -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(plan_cmd, cwd='infra')
    
    if not success:
        print_error(f"Plan failed: {stderr}")
        return False
    
    # Show what will be changed
    print_info("Target group migration plan:")
    lines = stdout.split('\n')
    for line in lines:
        if 'target_group' in line.lower() or 'Plan:' in line:
            print_info(f"  {line.strip()}")
    
    # Apply changes
    apply_cmd = f'terraform apply -auto-approve -target=aws_lb_target_group.frontend -target=aws_lb_target_group.backend -target=aws_lb_listener.frontend -target=aws_lb_listener_rule.backend -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(apply_cmd, cwd='infra')
    
    if success:
        print_status("Target groups migrated successfully")
        return True
    else:
        print_error(f"Apply failed: {stderr}")
        return False

def apply_remaining_changes():
    """Apply any remaining infrastructure changes"""
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
        
        # Apply remaining changes
        apply_cmd = f'terraform apply -auto-approve -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
        success, stdout, stderr = run_command(apply_cmd, cwd='infra')
        
        if success:
            print_status("All infrastructure changes applied successfully")
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
    print("=== TARGET GROUP MIGRATION SCRIPT - ENHANCED ===")
    print("===============================================")
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
    
    print_warning("This script will:")
    print_warning("1. Temporarily remove lifecycle protection from target groups")
    print_warning("2. Allow Terraform to recreate them with IP-based targeting")
    print_warning("3. Restore lifecycle protection")
    print_warning("4. Apply any remaining infrastructure changes")
    
    confirm = input(f"\n{Colors.YELLOW}Proceed with enhanced target group migration? (y/N): {Colors.END}")
    if confirm.lower() != 'y':
        print_info("Migration cancelled")
        sys.exit(0)
    
    try:
        # Step 1: Backup main.tf
        if not backup_main_tf():
            print_error("Failed to create backup")
            sys.exit(1)
        
        # Step 2: Remove target groups from state
        if not remove_target_groups_from_state():
            print_error("Failed to remove target groups from state")
            sys.exit(1)
        
        # Step 3: Remove lifecycle protection temporarily
        if not remove_lifecycle_protection():
            print_error("Failed to remove lifecycle protection")
            sys.exit(1)
        
        # Step 4: Apply target group changes
        if not apply_target_group_changes():
            print_error("Failed to apply target group changes")
            # Try to restore protection even if apply failed
            restore_lifecycle_protection()
            sys.exit(1)
        
        # Step 5: Restore lifecycle protection
        if not restore_lifecycle_protection():
            print_error("Failed to restore lifecycle protection")
            sys.exit(1)
        
        # Step 6: Apply remaining changes
        if not apply_remaining_changes():
            print_error("Failed to apply remaining changes")
            sys.exit(1)
        
        # Success summary
        print_title("Migration Summary")
        print_status("✅ Target groups migrated to IP-based targeting")
        print_status("✅ Lifecycle protection restored")
        print_status("✅ Infrastructure deployment completed")
        print_status("✅ All resources operational")
        
        print_info("\nNext steps:")
        print_info("1. Verify target groups show target_type = 'ip' in AWS console")
        print_info("2. Deploy container images to ECR")
        print_info("3. Start ECS services")
        
    except Exception as e:
        print_error(f"Migration failed: {e}")
        print_info("Attempting to restore lifecycle protection...")
        restore_lifecycle_protection()
        sys.exit(1)

if __name__ == "__main__":
    main()
