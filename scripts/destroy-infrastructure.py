#!/usr/bin/env python3
"""
Safe AWS Infrastructure Destroy Script
- Removes AWS resources for clean slate testing
- Preserves data by default (S3, RDS snapshots)
- Provides selective destruction options
- Safety confirmations for destructive operations
"""

import subprocess
import json
import sys
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

def get_destruction_mode():
    """Get user's preferred destruction mode"""
    print_title("Destruction Mode Selection")
    print("Choose destruction level:")
    print("1. 🔄 SOFT DESTROY - Remove compute resources, keep data (S3, RDS)")
    print("2. 🧹 MEDIUM DESTROY - Remove most resources, create RDS snapshot")
    print("3. 💥 FULL DESTROY - Remove everything (DANGEROUS)")
    print("4. 🎯 SELECTIVE DESTROY - Choose specific resources")
    print("5. ❌ CANCEL")
    
    while True:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            return "soft"
        elif choice == "2":
            return "medium"
        elif choice == "3":
            return "full"
        elif choice == "4":
            return "selective"
        elif choice == "5":
            print_info("Operation cancelled")
            return None
        else:
            print_warning("Invalid choice. Please enter 1-5.")

def confirm_destruction(mode, account_id):
    """Get final confirmation for destruction"""
    print_title("DESTRUCTION CONFIRMATION")
    print_warning(f"You are about to destroy AWS resources in account: {account_id}")
    print_warning(f"Region: {AWS_REGION}")
    print_warning(f"Mode: {mode.upper()}")
    
    if mode == "full":
        print_error("⚠️  FULL DESTROY will delete ALL data including S3 and RDS!")
        print_error("⚠️  This action is IRREVERSIBLE!")
        
        confirm1 = input("Type 'DELETE ALL DATA' to confirm full destruction: ")
        if confirm1 != "DELETE ALL DATA":
            print_info("Full destruction cancelled")
            return False
    
    final_confirm = input(f"Are you sure you want to proceed with {mode} destroy? (yes/no): ")
    return final_confirm.lower() == "yes"

def remove_lifecycle_protection():
    """Remove lifecycle protection from Terraform configuration"""
    print_title("Removing Lifecycle Protection")
    
    main_tf_path = Path('infra/main.tf')
    if not main_tf_path.exists():
        print_error("main.tf not found")
        return False
    
    # Read current main.tf
    with open(main_tf_path, 'r') as f:
        content = f.read()
    
    # Remove lifecycle blocks
    lines = content.split('\n')
    filtered_lines = []
    skip_block = False
    brace_count = 0
    
    for line in lines:
        if 'lifecycle {' in line:
            skip_block = True
            brace_count = 1
            continue
        
        if skip_block:
            if '{' in line:
                brace_count += line.count('{')
            if '}' in line:
                brace_count -= line.count('}')
                if brace_count == 0:
                    skip_block = False
            continue
        
        filtered_lines.append(line)
    
    # Write modified content
    modified_content = '\n'.join(filtered_lines)
    with open(main_tf_path, 'w') as f:
        f.write(modified_content)
    
    print_status("Lifecycle protection removed")
    return True

def restore_lifecycle_protection():
    """Restore lifecycle protection to Terraform configuration"""
    print_info("Restoring lifecycle protection...")
    
    # Reset to original state
    success, stdout, stderr = run_command('git checkout infra/main.tf')
    if success:
        print_status("Lifecycle protection restored")
    else:
        print_warning("Could not restore lifecycle protection automatically")

def create_rds_snapshot():
    """Create RDS snapshot before destruction"""
    print_info("Creating RDS snapshot before destruction...")
    
    db_identifier = f"{APP_NAME}-{ENVIRONMENT}-db"
    snapshot_id = f"{db_identifier}-final-snapshot-{int(time.time())}"
    
    cmd = f'aws rds create-db-snapshot --db-instance-identifier {db_identifier} --db-snapshot-identifier {snapshot_id} --region {AWS_REGION}'
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print_status(f"RDS snapshot created: {snapshot_id}")
        return snapshot_id
    else:
        print_warning(f"Could not create RDS snapshot: {stderr}")
        return None

def selective_destroy():
    """Allow user to select specific resources to destroy"""
    print_title("Selective Resource Destruction")
    
    resources = {
        "1": ("ECS Services", "Safe - just stops running containers"),
        "2": ("ECS Task Definitions", "Safe - can be recreated"),
        "3": ("Load Balancer & Target Groups", "Moderate - affects traffic routing"),
        "4": ("ECS Cluster", "Safe - just container orchestration"),
        "5": ("ECR Repositories", "Caution - removes container images"),
        "6": ("CloudWatch Log Groups", "Caution - removes logs"),
        "7": ("IAM Roles", "Safe - can be recreated"),
        "8": ("Security Groups", "Safe - can be recreated"),
        "9": ("NAT Gateways", "Moderate - affects private subnet internet"),
        "10": ("RDS Database", "DANGEROUS - data loss"),
        "11": ("S3 Bucket", "DANGEROUS - data loss"),
        "12": ("VPC & Networking", "Safe - can be recreated")
    }
    
    print("Select resources to destroy (comma-separated, e.g., 1,2,3):")
    for key, (name, risk) in resources.items():
        print(f"{key}. {name} - {risk}")
    
    selection = input("\nEnter selections: ").strip()
    
    try:
        selected = [resources[s.strip()] for s in selection.split(',') if s.strip() in resources]
        if selected:
            print_info("Selected resources:")
            for name, risk in selected:
                print(f"  • {name} - {risk}")
            return True
        else:
            print_warning("No valid selections made")
            return False
    except:
        print_error("Invalid selection format")
        return False

def terraform_destroy(mode):
    """Run Terraform destroy with appropriate targeting"""
    print_title(f"Running Terraform Destroy - {mode.upper()} Mode")
    
    if not Path('infra/main.tf').exists():
        print_error("Terraform configuration not found")
        return False
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    success, stdout, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print_error(f"Terraform init failed: {stderr}")
        return False
    
    # Build destroy command based on mode
    if mode == "soft":
        # Only destroy ECS services, task definitions, and compute resources
        targets = [
            "aws_ecs_service.frontend",
            "aws_ecs_service.backend", 
            "aws_ecs_task_definition.frontend",
            "aws_ecs_task_definition.backend",
            "aws_cloudwatch_log_group.frontend",
            "aws_cloudwatch_log_group.backend"
        ]
        
        destroy_cmd = f'terraform destroy -auto-approve -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
        for target in targets:
            destroy_cmd += f' -target={target}'
            
    elif mode == "medium":
        # Exclude S3 and RDS from destruction
        destroy_cmd = f'terraform destroy -auto-approve -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
        
        # Remove S3 and RDS from state so they're not destroyed
        print_info("Removing S3 and RDS from Terraform state (preserving actual resources)...")
        run_command('terraform state rm aws_s3_bucket.main', cwd='infra')
        run_command('terraform state rm aws_s3_bucket_versioning.main', cwd='infra')
        run_command('terraform state rm aws_s3_bucket_server_side_encryption_configuration.main', cwd='infra')
        run_command('terraform state rm aws_s3_bucket_cors_configuration.main', cwd='infra')
        run_command('terraform state rm aws_db_instance.main', cwd='infra')
        run_command('terraform state rm aws_db_subnet_group.main', cwd='infra')
        run_command('terraform state rm random_password.db_password', cwd='infra')
        
    else:  # full destroy
        destroy_cmd = f'terraform destroy -auto-approve -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    
    # Execute destroy
    print_info("Executing Terraform destroy...")
    success, stdout, stderr = run_command(destroy_cmd, cwd='infra')
    
    if success:
        print_status("Terraform destroy completed successfully")
        return True
    else:
        print_error(f"Terraform destroy failed: {stderr}")
        return False

def cleanup_remaining_resources():
    """Clean up any remaining AWS resources not managed by Terraform"""
    print_title("Cleaning Up Remaining Resources")
    
    # Clean up any orphaned resources
    print_info("Checking for orphaned resources...")
    
    # List any remaining resources
    cmd = f'aws elbv2 describe-load-balancers --region {AWS_REGION}'
    success, stdout, stderr = run_command(cmd)
    
    if success and stdout:
        try:
            data = json.loads(stdout)
            lbs = [lb for lb in data.get('LoadBalancers', []) if APP_NAME in lb.get('LoadBalancerName', '')]
            if lbs:
                print_warning(f"Found {len(lbs)} orphaned load balancers")
        except:
            pass
    
    print_info("Manual cleanup may be required for some resources")

def main():
    """Main destroy function"""
    print(f"{Colors.RED}")
    print("=== AWS INFRASTRUCTURE DESTROY SCRIPT ===")
    print("==========================================")
    print("⚠️  WARNING: This will destroy AWS resources!")
    print(f"Region: {AWS_REGION} | Environment: {ENVIRONMENT}")
    print(f"{Colors.END}")
    
    # Check AWS credentials
    creds_ok, account_id = check_aws_credentials()
    if not creds_ok:
        sys.exit(1)
    
    # Get destruction mode
    mode = get_destruction_mode()
    if not mode:
        sys.exit(0)
    
    # Handle selective mode
    if mode == "selective":
        if not selective_destroy():
            sys.exit(0)
        mode = "selective"
    
    # Get final confirmation
    if not confirm_destruction(mode, account_id):
        print_info("Destruction cancelled")
        sys.exit(0)
    
    # Create RDS snapshot for medium/full destroy
    if mode in ["medium", "full"]:
        import time
        create_rds_snapshot()
    
    # Remove lifecycle protection
    if not remove_lifecycle_protection():
        print_error("Could not remove lifecycle protection")
        sys.exit(1)
    
    try:
        # Perform destruction
        if terraform_destroy(mode):
            print_status("🎉 Infrastructure destruction completed!")
            
            # Clean up remaining resources
            cleanup_remaining_resources()
            
            print_title("Post-Destruction Summary")
            if mode == "soft":
                print_status("✅ Compute resources destroyed")
                print_info("📊 Data preserved (S3, RDS)")
            elif mode == "medium":
                print_status("✅ Most resources destroyed")
                print_info("📊 S3 and RDS preserved")
            else:
                print_status("✅ All resources destroyed")
                print_warning("📊 All data deleted")
            
            print_info("\nTo redeploy from clean slate:")
            print_info("python scripts/deploy-infrastructure.py")
            
        else:
            print_error("❌ Infrastructure destruction failed")
            
    finally:
        # Always restore lifecycle protection
        restore_lifecycle_protection()

if __name__ == "__main__":
    main()
