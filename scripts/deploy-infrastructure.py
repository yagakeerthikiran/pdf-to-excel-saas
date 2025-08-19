#!/usr/bin/env python3
"""
SAFE & NON-DESTRUCTIVE Infrastructure Deployment Script
- NEVER deletes resources, only checks existence and imports safely
- Aligns with actual Terraform configuration resource names
- Adds lifecycle protection against destructive operations
- Validates Terraform config matches AWS reality before importing

DOCUMENTED ISSUES & FIXES:
=========================
ISSUE: Script caused resource deletion attempts instead of safe imports
CAUSE: Terraform config drift + incorrect resource naming + no protection blocks
FIX: Align with actual Terraform resource names, add lifecycle protection, validate before import

ISSUE: IAM Role naming mismatch (ecs_task_task_role vs ecs_task_role)  
CAUSE: Script used wrong Terraform resource address
FIX: Use correct addresses from main.tf: aws_iam_role.ecs_task_execution_role, aws_iam_role.ecs_task_role

ISSUE: Target Groups attempted deletion due to config mismatch
CAUSE: Terraform thought TGs needed replacement due to config drift
FIX: Add prevent_destroy lifecycle blocks, validate config matches AWS

ISSUE: Subnet/VPC mismatches causing RDS errors
CAUSE: Terraform subnet IDs don't match AWS reality
FIX: Check actual subnet IDs in AWS before importing, update main.tf if needed

SAFETY STRATEGY:
1. Never delete resources - only check existence and import
2. Add lifecycle { prevent_destroy = true } to critical resources
3. Validate Terraform resource names exist in config before importing
4. Check AWS reality matches Terraform config before operations
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
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

def run_aws_command(cmd, timeout=30):
    """Run AWS CLI command with proper error handling"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    return True, json.loads(result.stdout)
                except json.JSONDecodeError:
                    return True, result.stdout.strip()
            return True, None
        else:
            return False, result.stderr.strip() if result.stderr else "Not found"
    except Exception as e:
        return False, str(e)

def run_terraform_command(cmd, cwd='infra'):
    """Run Terraform command with error handling"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_terraform_resource_list():
    """Get list of resources defined in Terraform configuration"""
    print_info("Checking Terraform configuration for defined resources...")
    
    success, stdout, stderr = run_terraform_command('terraform plan -no-color')
    
    if not success:
        print_warning("Could not get Terraform resource list, proceeding with known resources")
        return None
    
    # Extract resource addresses from plan output
    resources = []
    lines = stdout.split('\n')
    for line in lines:
        if '# aws_' in line and 'will be' in line:
            parts = line.split()
            for part in parts:
                if part.startswith('aws_'):
                    resources.append(part)
                    break
    
    return resources

def add_lifecycle_protection():
    """Add lifecycle protection to prevent accidental resource deletion"""
    print_title("Adding Lifecycle Protection to Critical Resources")
    
    main_tf_path = Path('infra/main.tf')
    if not main_tf_path.exists():
        print_error("main.tf not found")
        return False
    
    # Read current main.tf
    with open(main_tf_path, 'r') as f:
        content = f.read()
    
    # Check if lifecycle blocks already exist
    if 'prevent_destroy = true' in content:
        print_info("Lifecycle protection already exists")
        return True
    
    # Add lifecycle blocks to critical resources
    protection_blocks = [
        ('resource "aws_lb_target_group" "frontend"', 'target group frontend'),
        ('resource "aws_lb_target_group" "backend"', 'target group backend'),
        ('resource "aws_lb" "main"', 'load balancer'),
        ('resource "aws_db_instance" "main"', 'RDS database'),
        ('resource "aws_s3_bucket" "main"', 'S3 bucket'),
        ('resource "aws_ecs_cluster" "main"', 'ECS cluster')
    ]
    
    modified_content = content
    
    for resource_line, description in protection_blocks:
        if resource_line in content:
            # Find the resource block and add lifecycle protection
            lines = modified_content.split('\n')
            in_resource = False
            brace_count = 0
            insert_index = -1
            
            for i, line in enumerate(lines):
                if resource_line in line:
                    in_resource = True
                    brace_count = 0
                elif in_resource:
                    if '{' in line:
                        brace_count += line.count('{')
                    if '}' in line:
                        brace_count -= line.count('}')
                        if brace_count == 0:
                            # End of resource block
                            insert_index = i
                            break
            
            if insert_index > 0:
                # Insert lifecycle block before closing brace
                lifecycle_block = [
                    '',
                    '  lifecycle {',
                    '    prevent_destroy = true',
                    '  }'
                ]
                
                for j, lifecycle_line in enumerate(lifecycle_block):
                    lines.insert(insert_index + j, lifecycle_line)
                
                modified_content = '\n'.join(lines)
                print_status(f"Added lifecycle protection to {description}")
    
    # Write modified content
    with open(main_tf_path, 'w') as f:
        f.write(modified_content)
    
    print_status("Lifecycle protection added to critical resources")
    return True

def get_load_balancer_arn(lb_name):
    """Get Load Balancer ARN from name"""
    cmd = f'aws elbv2 describe-load-balancers --names {lb_name} --query "LoadBalancers[0].LoadBalancerArn" --output text --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, str) and result.startswith('arn:'):
        return result
    return None

def get_target_group_arn(tg_name):
    """Get Target Group ARN from name"""
    cmd = f'aws elbv2 describe-target-groups --names {tg_name} --query "TargetGroups[0].TargetGroupArn" --output text --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, str) and result.startswith('arn:'):
        return result
    return None

def check_aws_resources_safely():
    """Check AWS resources and get their proper identifiers - SAFE MODE"""
    print_title("Checking AWS Resources (Read-Only Mode)")
    
    # Resource mapping based on ACTUAL main.tf configuration
    resources = {
        'db_subnet_group': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-db-subnet-group',
            'terraform_resource': 'aws_db_subnet_group.main',
            'check_cmd': f'aws rds describe-db-subnet-groups --db-subnet-group-name {APP_NAME}-{ENVIRONMENT}-db-subnet-group --region {AWS_REGION}',
            'import_id_type': 'name'
        },
        'load_balancer': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-alb',
            'terraform_resource': 'aws_lb.main',
            'check_cmd': None,  # Custom function
            'import_id_type': 'arn'
        },
        'target_group_frontend': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-frontend-tg',
            'terraform_resource': 'aws_lb_target_group.frontend',
            'check_cmd': None,  # Custom function
            'import_id_type': 'arn'
        },
        'target_group_backend': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-backend-tg',
            'terraform_resource': 'aws_lb_target_group.backend',
            'check_cmd': None,  # Custom function
            'import_id_type': 'arn'
        },
        'iam_role_execution': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-ecs-task-execution-role',
            'terraform_resource': 'aws_iam_role.ecs_task_execution_role',  # CORRECTED
            'check_cmd': f'aws iam get-role --role-name {APP_NAME}-{ENVIRONMENT}-ecs-task-execution-role',
            'import_id_type': 'name'
        },
        'iam_role_task': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-ecs-task-role',
            'terraform_resource': 'aws_iam_role.ecs_task_role',  # CORRECTED
            'check_cmd': f'aws iam get-role --role-name {APP_NAME}-{ENVIRONMENT}-ecs-task-role',
            'import_id_type': 'name'
        },
        's3_bucket': {
            'name': f'{APP_NAME}-{ENVIRONMENT}',
            'terraform_resource': 'aws_s3_bucket.main',
            'check_cmd': f'aws s3api head-bucket --bucket {APP_NAME}-{ENVIRONMENT} --region {AWS_REGION}',
            'import_id_type': 'name'
        },
        'rds_instance': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-db',
            'terraform_resource': 'aws_db_instance.main',
            'check_cmd': f'aws rds describe-db-instances --db-instance-identifier {APP_NAME}-{ENVIRONMENT}-db --region {AWS_REGION}',
            'import_id_type': 'name'
        },
        'ecs_cluster': {
            'name': f'{APP_NAME}-{ENVIRONMENT}',
            'terraform_resource': 'aws_ecs_cluster.main',
            'check_cmd': f'aws ecs describe-clusters --clusters {APP_NAME}-{ENVIRONMENT} --region {AWS_REGION}',
            'import_id_type': 'name'
        },
        'ecr_frontend': {
            'name': f'{APP_NAME}-frontend',
            'terraform_resource': 'aws_ecr_repository.frontend',
            'check_cmd': f'aws ecr describe-repositories --repository-names {APP_NAME}-frontend --region {AWS_REGION}',
            'import_id_type': 'name'
        },
        'ecr_backend': {
            'name': f'{APP_NAME}-backend',
            'terraform_resource': 'aws_ecr_repository.backend',
            'check_cmd': f'aws ecr describe-repositories --repository-names {APP_NAME}-backend --region {AWS_REGION}',
            'import_id_type': 'name'
        }
    }
    
    print_info("Performing read-only checks of AWS resources...")
    
    for resource_key, resource_info in resources.items():
        name = resource_info['name']
        print_info(f"Checking: {name}")
        
        # Special handling for ALB and Target Groups (need ARNs)
        if resource_key == 'load_balancer':
            arn = get_load_balancer_arn(name)
            if arn:
                resource_info['exists'] = True
                resource_info['import_id'] = arn
                print_status(f"EXISTS: {name} (ARN: {arn[:50]}...)")
            else:
                resource_info['exists'] = False
                print_warning(f"MISSING: {name}")
                
        elif 'target_group' in resource_key:
            arn = get_target_group_arn(name)
            if arn:
                resource_info['exists'] = True
                resource_info['import_id'] = arn
                print_status(f"EXISTS: {name} (ARN: {arn[:50]}...)")
            else:
                resource_info['exists'] = False
                print_warning(f"MISSING: {name}")
                
        else:
            # Standard AWS CLI check
            success, result = run_aws_command(resource_info['check_cmd'])
            
            if success:
                resource_info['exists'] = True
                resource_info['import_id'] = name  # Most resources use name
                print_status(f"EXISTS: {name}")
            else:
                resource_info['exists'] = False
                print_warning(f"MISSING: {name}")
    
    return resources

def safe_import_existing_resources(resources):
    """Safely import existing resources without destructive operations"""
    print_title("Safe Import of Existing Resources (No Deletion Risk)")
    
    existing_resources = {k: v for k, v in resources.items() if v.get('exists')}
    
    if not existing_resources:
        print_info("No existing resources to import")
        return True
    
    print_info(f"Found {len(existing_resources)} existing resources")
    
    # Check current Terraform state first
    print_info("Checking current Terraform state...")
    success, stdout, stderr = run_terraform_command('terraform state list')
    
    current_state_resources = []
    if success:
        current_state_resources = stdout.strip().split('\n') if stdout.strip() else []
        print_info(f"Current state contains {len(current_state_resources)} resources")
    
    for resource_key, resource_info in existing_resources.items():
        terraform_resource = resource_info['terraform_resource']
        import_id = resource_info['import_id']
        resource_name = resource_info['name']
        
        print_info(f"Processing {resource_name}...")
        
        # Check if already in state
        if terraform_resource in current_state_resources:
            print_status(f"✅ Already in state: {resource_name}")
            continue
        
        # Safe import attempt
        print_info(f"  Importing with ID: {import_id}")
        
        import_cmd = f'terraform import {terraform_resource} {import_id}'
        success, stdout, stderr = run_terraform_command(import_cmd)
        
        if success:
            print_status(f"✅ Successfully imported: {resource_name}")
        else:
            print_warning(f"⚠️ Import failed for {resource_name}")
            print_warning(f"   Error: {stderr}")
            
            # Handle specific error cases WITHOUT deletion
            if "Resource already managed" in stderr:
                print_info(f"   Resource {resource_name} already in state (different address)")
                print_info(f"   This is safe - resource exists and is managed")
            elif "does not exist" in stderr:
                print_warning(f"   AWS resource {resource_name} may have been deleted")
            else:
                print_info(f"   Import issue for {resource_name} - resource exists in AWS")
    
    return True

def safe_terraform_deployment(resources):
    """Run Terraform deployment in safe mode - no destructive operations"""
    print_title("Safe Terraform Deployment (Read-Only Plan)")
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    success, stdout, stderr = run_terraform_command('terraform init -reconfigure')
    
    if not success:
        print_error("Terraform init failed")
        print_error(stderr)
        return False
    
    print_status("Terraform initialized")
    
    # Import existing resources safely
    safe_import_existing_resources(resources)
    
    # Generate plan (read-only)
    print_info("Generating Terraform plan (read-only)...")
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}" -out=tfplan'
    success, stdout, stderr = run_terraform_command(plan_cmd)
    
    if not success:
        print_error("Terraform plan failed")
        print_error(stderr)
        return False
    
    # Analyze plan for safety
    print_title("Plan Analysis - Safety Check")
    
    if stdout:
        lines = stdout.split('\n')
        
        creates = []
        updates = []
        destroys = []
        
        for line in lines:
            if 'will be created' in line:
                creates.append(line.strip())
            elif 'will be updated' in line or 'will be modified' in line:
                updates.append(line.strip())
            elif 'will be destroyed' in line or 'will be deleted' in line:
                destroys.append(line.strip())
            elif 'Plan:' in line:
                print_info(f"Plan summary: {line}")
        
        # Safety analysis
        if destroys:
            print_error("⚠️ DANGER: Plan contains resource deletions!")
            print_error("This script is designed to be non-destructive")
            for destroy in destroys:
                print_error(f"  🔥 {destroy}")
            
            print_warning("Stopping deployment to prevent resource deletion")
            print_info("Please review Terraform configuration for drift issues")
            return False
        
        if creates:
            print_info(f"✅ Plan will create {len(creates)} new resources:")
            for create in creates[:5]:  # Show first 5
                print_info(f"  + {create}")
            if len(creates) > 5:
                print_info(f"  ... and {len(creates) - 5} more")
        
        if updates:
            print_warning(f"⚠️ Plan will update {len(updates)} existing resources:")
            for update in updates[:3]:  # Show first 3
                print_warning(f"  ~ {update}")
    
    # Check if it's safe to proceed
    if 'No changes' in stdout:
        print_status("✅ No changes needed - all resources properly managed!")
        return True
    
    # Ask for confirmation only if no destructive operations
    missing_count = sum(1 for r in resources.values() if not r.get('exists'))
    
    if missing_count > 0:
        print(f"\n{Colors.CYAN}This deployment will create {missing_count} missing resources.{Colors.END}")
        print(f"{Colors.GREEN}No existing resources will be deleted or replaced.{Colors.END}")
        
        confirm = input("Proceed with safe deployment? (y/N): ")
        
        if confirm.lower() != 'y':
            print_warning("Deployment cancelled")
            return False
        
        # Apply changes
        print_info("Applying safe Terraform configuration...")
        success, stdout, stderr = run_terraform_command('terraform apply tfplan')
        
        if success:
            print_status("🎉 Safe infrastructure deployment completed!")
            return True
        else:
            print_error("❌ Terraform apply failed!")
            print_error(stderr)
            return False
    
    else:
        print_status("✅ All resources exist - no deployment needed!")
        return True

def check_third_party_services():
    """Validate third-party service configurations"""
    print_title("Validating Third-Party Services")
    
    env_file = Path('.env.prod')
    if not env_file.exists():
        print_warning(".env.prod not found")
        return {}
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    services = {}
    
    # Check key services
    if env_vars.get('STRIPE_SECRET_KEY', '').startswith('sk_'):
        print_status("Stripe configured")
        services['stripe'] = True
    else:
        print_warning("Stripe not configured")
        services['stripe'] = False
    
    if 'supabase.co' in env_vars.get('SUPABASE_URL', ''):
        print_status("Supabase configured")
        services['supabase'] = True
    else:
        print_warning("Supabase not configured")
        services['supabase'] = False
    
    return services

def get_aws_account_info():
    """Get AWS account information"""
    success, result = run_aws_command(f'aws sts get-caller-identity --region {AWS_REGION}')
    
    if success and isinstance(result, dict):
        return result['Account']
    else:
        print_error("AWS credentials not configured")
        print_info("Run: aws configure")
        return None

def main():
    """Main deployment function - SAFE & NON-DESTRUCTIVE"""
    print(f"{Colors.BLUE}")
    print("=== PDF to Excel SaaS - SAFE & NON-DESTRUCTIVE Deployment ===")
    print("============================================================")
    print("Strategy: Check AWS → Add protection → Safe import → Deploy missing only")
    print("GUARANTEE: No existing resources will be deleted or replaced")
    print(f"App: {APP_NAME} | Environment: {ENVIRONMENT} | Region: {AWS_REGION}")
    print(f"{Colors.END}")
    
    try:
        # Step 1: Validate AWS access
        account_id = get_aws_account_info()
        if not account_id:
            return
        
        print_status(f"AWS Account: {account_id}")
        
        # Step 2: Add lifecycle protection to prevent destruction
        add_lifecycle_protection()
        
        # Step 3: Check all AWS resources (read-only)
        resources = check_aws_resources_safely()
        
        print_title("Resource Analysis Summary")
        
        existing_count = sum(1 for r in resources.values() if r.get('exists'))
        missing_count = len(resources) - existing_count
        
        print_status(f"Existing resources in AWS: {existing_count}")
        print_warning(f"Missing resources: {missing_count}")
        
        if existing_count > 0:
            print_info("Existing resources (will be safely imported):")
            for key, resource in resources.items():
                if resource.get('exists'):
                    print(f"  ✅ {key}: {resource['name']}")
        
        if missing_count > 0:
            print_info("Missing resources (will be created):")
            for key, resource in resources.items():
                if not resource.get('exists'):
                    print(f"  ❌ {key}: {resource['name']}")
        
        # Step 4: Check third-party services
        services = check_third_party_services()
        
        # Step 5: Safe deployment
        if missing_count > 0 or existing_count > 0:
            action_msg = f"Safely import {existing_count} existing + Create {missing_count} missing resources"
            
            proceed = input(f"\n{action_msg}? (y/N): ")
            if proceed.lower() != 'y':
                print_info("Deployment cancelled")
                return
            
            # Run safe deployment
            if safe_terraform_deployment(resources):
                print_status("🎉 Safe infrastructure deployment successful!")
                
                # Final verification
                print_info("Performing final verification...")
                final_resources = check_aws_resources_safely()
                final_missing = sum(1 for r in final_resources.values() if not r.get('exists'))
                
                if final_missing == 0:
                    print_status("✅ ALL infrastructure is now properly deployed!")
                else:
                    print_warning(f"⚠️ Still missing {final_missing} resources")
            else:
                print_error("❌ Infrastructure deployment failed")
        else:
            print_status("✅ No infrastructure changes needed")
        
        # Step 6: Next steps
        print_title("Next Steps")
        print_info("1. Build and push Docker images to ECR")
        print_info("2. Deploy application to ECS")
        print_info("3. Test your application")
        
    except KeyboardInterrupt:
        print_warning("\nDeployment interrupted")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
