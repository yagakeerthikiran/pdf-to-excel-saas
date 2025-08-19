#!/usr/bin/env python3
"""
TRULY RESUME-SAFE Infrastructure Deployment Script
- FIXED: Comprehensive AWS resource detection to avoid "already exists" errors
- Always checks actual AWS state vs requirements
- Only creates/updates what's truly missing or misaligned

DOCUMENTED ISSUES & FIXES:
=========================
ISSUE: Script shows resources as "MISSING" but Terraform gets "already exists" errors
CAUSE: Incomplete AWS resource detection - script missed existing Load Balancer, DB Subnet Group, etc.
FIX: Enhanced resource detection with proper AWS CLI commands and error handling
AFFECTED: All AWS resource checking functions - now comprehensive and accurate

ISSUE: Target groups detected as existing but Load Balancer shown as missing  
CAUSE: Load Balancer detection used wrong AWS CLI command format
FIX: Corrected aws elbv2 describe-load-balancers command syntax

ISSUE: IAM roles detected as existing but still causing "already exists" errors
CAUSE: AWS resource detection vs Terraform state mismatch
FIX: Added resource import capability to sync Terraform state with AWS reality
"""

import os
import sys
import subprocess
import json
import time
import re
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
            # For resource checking, "not found" is not an error
            return False, result.stderr.strip() if result.stderr else "Not found"
    except Exception as e:
        return False, str(e)

def check_db_subnet_group_exists(name):
    """Check if RDS DB Subnet Group exists"""
    cmd = f'aws rds describe-db-subnet-groups --db-subnet-group-name {name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        return len(result.get('DBSubnetGroups', [])) > 0
    return False

def check_load_balancer_exists(name):
    """Check if Application Load Balancer exists"""
    # First try by name
    cmd = f'aws elbv2 describe-load-balancers --names {name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        return len(result.get('LoadBalancers', [])) > 0
    
    # If name search fails, search all load balancers for the name
    cmd = f'aws elbv2 describe-load-balancers --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        for lb in result.get('LoadBalancers', []):
            if name in lb.get('LoadBalancerName', ''):
                return True
    
    return False

def check_target_group_exists(name):
    """Check if Target Group exists"""
    cmd = f'aws elbv2 describe-target-groups --names {name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        return len(result.get('TargetGroups', [])) > 0
    return False

def check_iam_role_exists(name):
    """Check if IAM Role exists"""
    cmd = f'aws iam get-role --role-name {name}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        return 'Role' in result
    return False

def check_s3_bucket_exists(name):
    """Check if S3 bucket exists"""
    cmd = f'aws s3api head-bucket --bucket {name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    return success

def check_rds_instance_exists(name):
    """Check if RDS instance exists"""
    cmd = f'aws rds describe-db-instances --db-instance-identifier {name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        return len(result.get('DBInstances', [])) > 0
    return False

def check_ecs_cluster_exists(name):
    """Check if ECS cluster exists and is active"""
    cmd = f'aws ecs describe-clusters --clusters {name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        clusters = result.get('clusters', [])
        for cluster in clusters:
            if cluster.get('status') == 'ACTIVE' and cluster.get('clusterName') == name:
                return True
    return False

def check_ecr_repository_exists(name):
    """Check if ECR repository exists"""
    cmd = f'aws ecr describe-repositories --repository-names {name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        return len(result.get('repositories', [])) > 0
    return False

def comprehensive_aws_scan():
    """Comprehensive scan of ALL AWS resources for this application"""
    print_title("Comprehensive AWS Infrastructure Scan")
    
    resources = {
        'db_subnet_group': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-db-subnet-group',
            'check_func': check_db_subnet_group_exists,
            'terraform_resource': 'aws_db_subnet_group.main'
        },
        'load_balancer': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-alb',
            'check_func': check_load_balancer_exists,
            'terraform_resource': 'aws_lb.main'
        },
        'target_group_frontend': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-frontend-tg',
            'check_func': check_target_group_exists,
            'terraform_resource': 'aws_lb_target_group.frontend'
        },
        'target_group_backend': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-backend-tg',
            'check_func': check_target_group_exists,
            'terraform_resource': 'aws_lb_target_group.backend'
        },
        'iam_role_execution': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-ecs-task-execution-role',
            'check_func': check_iam_role_exists,
            'terraform_resource': 'aws_iam_role.ecs_task_execution_role'
        },
        'iam_role_task': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-ecs-task-role',
            'check_func': check_iam_role_exists,
            'terraform_resource': 'aws_iam_role.ecs_task_role'
        },
        's3_bucket': {
            'name': f'{APP_NAME}-{ENVIRONMENT}',
            'check_func': check_s3_bucket_exists,
            'terraform_resource': 'aws_s3_bucket.main'
        },
        'rds_instance': {
            'name': f'{APP_NAME}-{ENVIRONMENT}-db',
            'check_func': check_rds_instance_exists,
            'terraform_resource': 'aws_db_instance.main'
        },
        'ecs_cluster': {
            'name': f'{APP_NAME}-{ENVIRONMENT}',
            'check_func': check_ecs_cluster_exists,
            'terraform_resource': 'aws_ecs_cluster.main'
        },
        'ecr_frontend': {
            'name': f'{APP_NAME}-frontend',
            'check_func': check_ecr_repository_exists,
            'terraform_resource': 'aws_ecr_repository.frontend'
        },
        'ecr_backend': {
            'name': f'{APP_NAME}-backend',
            'check_func': check_ecr_repository_exists,
            'terraform_resource': 'aws_ecr_repository.backend'
        }
    }
    
    existing_resources = {}
    missing_resources = {}
    
    print_info("Checking each AWS resource with enhanced detection...")
    
    for resource_key, resource_info in resources.items():
        name = resource_info['name']
        check_func = resource_info['check_func']
        
        print_info(f"Checking: {name}")
        
        try:
            exists = check_func(name)
            
            if exists:
                existing_resources[resource_key] = resource_info
                print_status(f"EXISTS: {name}")
            else:
                missing_resources[resource_key] = resource_info
                print_warning(f"MISSING: {name}")
                
        except Exception as e:
            print_error(f"Error checking {name}: {e}")
            # Assume missing if we can't check
            missing_resources[resource_key] = resource_info
    
    return existing_resources, missing_resources

def create_terraform_import_script(existing_resources):
    """Create script to import existing resources into Terraform state"""
    print_title("Creating Terraform Import Strategy")
    
    if not existing_resources:
        print_info("No existing resources to import")
        return True
    
    import_commands = []
    
    # Map resources to their Terraform import syntax
    import_mapping = {
        'db_subnet_group': lambda name: f'terraform import aws_db_subnet_group.main {name}',
        'load_balancer': lambda name: f'terraform import aws_lb.main {name}',
        'target_group_frontend': lambda name: f'terraform import aws_lb_target_group.frontend {name}',
        'target_group_backend': lambda name: f'terraform import aws_lb_target_group.backend {name}',
        'iam_role_execution': lambda name: f'terraform import aws_iam_role.ecs_task_execution_role {name}',
        'iam_role_task': lambda name: f'terraform import aws_iam_role.ecs_task_role {name}',
        's3_bucket': lambda name: f'terraform import aws_s3_bucket.main {name}',
        'rds_instance': lambda name: f'terraform import aws_db_instance.main {name}',
        'ecs_cluster': lambda name: f'terraform import aws_ecs_cluster.main {name}',
        'ecr_frontend': lambda name: f'terraform import aws_ecr_repository.frontend {name}',
        'ecr_backend': lambda name: f'terraform import aws_ecr_repository.backend {name}'
    }
    
    for resource_key, resource_info in existing_resources.items():
        if resource_key in import_mapping:
            import_cmd = import_mapping[resource_key](resource_info['name'])
            import_commands.append(import_cmd)
            print_info(f"Will import: {resource_info['name']}")
    
    # Save import script
    import_script_content = "#!/bin/bash\n"
    import_script_content += "# Terraform Import Script - Auto-generated\n"
    import_script_content += f"# Generated: {datetime.now().isoformat()}\n\n"
    import_script_content += "cd infra\n\n"
    
    for cmd in import_commands:
        import_script_content += f"{cmd}\n"
    
    import_script_content += "\necho 'Import completed'\n"
    
    with open('import_existing_resources.sh', 'w') as f:
        f.write(import_script_content)
    
    print_status(f"Created import script with {len(import_commands)} commands")
    return True

def run_terraform_with_imports(existing_resources, missing_resources):
    """Run Terraform deployment with proper import handling"""
    print_title("Running Terraform with State Synchronization")
    
    os.makedirs('infra', exist_ok=True)
    
    # Clean start
    terraform_dirs = ['infra/.terraform', 'infra/.terraform.lock.hcl']
    for item in terraform_dirs:
        path = Path(item)
        if path.exists():
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    result = subprocess.run('terraform init -reconfigure', shell=True, cwd='infra', 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print_error("Terraform init failed")
        print_error(result.stderr)
        return False
    
    print_status("Terraform initialized")
    
    # Import existing resources first
    if existing_resources:
        print_info(f"Importing {len(existing_resources)} existing resources...")
        
        import_mapping = {
            'db_subnet_group': 'aws_db_subnet_group.main',
            'load_balancer': 'aws_lb.main', 
            'target_group_frontend': 'aws_lb_target_group.frontend',
            'target_group_backend': 'aws_lb_target_group.backend',
            'iam_role_execution': 'aws_iam_role.ecs_task_execution_role',
            'iam_role_task': 'aws_iam_role.ecs_task_role',
            's3_bucket': 'aws_s3_bucket.main',
            'rds_instance': 'aws_db_instance.main',
            'ecs_cluster': 'aws_ecs_cluster.main',
            'ecr_frontend': 'aws_ecr_repository.frontend',
            'ecr_backend': 'aws_ecr_repository.backend'
        }
        
        for resource_key, resource_info in existing_resources.items():
            if resource_key in import_mapping:
                terraform_resource = import_mapping[resource_key]
                resource_name = resource_info['name']
                
                print_info(f"Importing {resource_name}...")
                
                import_cmd = f'terraform import {terraform_resource} {resource_name}'
                result = subprocess.run(import_cmd, shell=True, cwd='infra', 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print_status(f"Imported: {resource_name}")
                else:
                    print_warning(f"Import failed for {resource_name}: {result.stderr}")
                    # Continue with other imports
    
    # Now plan deployment for missing resources
    print_info("Planning deployment for missing resources...")
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}" -out=tfplan'
    result = subprocess.run(plan_cmd, shell=True, cwd='infra', capture_output=True, text=True)
    
    if result.returncode != 0:
        print_error("Terraform plan failed")
        print_error(result.stderr)
        return False
    
    # Show what will be created
    if result.stdout:
        lines = result.stdout.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['Plan:', 'will be created', 'No changes']):
                print_info(f"Plan: {line}")
    
    # If nothing to create, we're done
    if 'No changes' in result.stdout:
        print_status("All resources already exist and are imported!")
        return True
    
    # Confirm deployment
    print(f"\n{Colors.YELLOW}[WARNING] This will create {len(missing_resources)} missing AWS resources.{Colors.END}")
    confirm = input("Proceed with deployment? (y/N): ")
    
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled")
        return False
    
    # Apply changes
    print_info("Applying Terraform configuration...")
    result = subprocess.run('terraform apply tfplan', shell=True, cwd='infra', 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print_status("Infrastructure deployment completed!")
        return True
    else:
        print_error("Terraform apply failed!")
        print_error(result.stderr)
        return False

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
    
    # Stripe
    if env_vars.get('STRIPE_SECRET_KEY', '').startswith('sk_'):
        print_status("Stripe configured")
        services['stripe'] = True
    else:
        print_warning("Stripe not configured")
        services['stripe'] = False
    
    # Supabase
    if 'supabase.co' in env_vars.get('SUPABASE_URL', ''):
        print_status("Supabase configured")
        services['supabase'] = True
    else:
        print_warning("Supabase not configured")
        services['supabase'] = False
    
    # Sentry
    if 'sentry.io' in env_vars.get('NEXT_PUBLIC_SENTRY_DSN', ''):
        print_status("Sentry configured")
        services['sentry'] = True
    else:
        print_warning("Sentry not configured")
        services['sentry'] = False
    
    # PostHog
    if env_vars.get('NEXT_PUBLIC_POSTHOG_KEY', ''):
        print_status("PostHog configured")
        services['posthog'] = True
    else:
        print_warning("PostHog not configured")
        services['posthog'] = False
    
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
    """Main deployment function - truly resume-safe with comprehensive checking"""
    print(f"{Colors.BLUE}")
    print("=== PDF to Excel SaaS - TRULY RESUME-SAFE Deployment ===")
    print("=======================================================")
    print("Strategy: Comprehensive AWS scan + Import existing + Deploy missing")
    print(f"App: {APP_NAME} | Environment: {ENVIRONMENT} | Region: {AWS_REGION}")
    print(f"{Colors.END}")
    
    try:
        # Step 1: Validate AWS access
        account_id = get_aws_account_info()
        if not account_id:
            return
        
        print_status(f"AWS Account: {account_id}")
        
        # Step 2: Comprehensive AWS infrastructure scan
        existing_resources, missing_resources = comprehensive_aws_scan()
        
        print_title("Infrastructure Analysis Summary")
        print_status(f"Existing resources: {len(existing_resources)}")
        print_warning(f"Missing resources: {len(missing_resources)}")
        
        if existing_resources:
            print_info("Existing resources (will be imported):")
            for key, resource in existing_resources.items():
                print(f"  ✅ {key}: {resource['name']}")
        
        if missing_resources:
            print_info("Missing resources (will be created):")
            for key, resource in missing_resources.items():
                print(f"  ❌ {key}: {resource['name']}")
        
        # Step 3: Check third-party services
        services = check_third_party_services()
        
        # Step 4: Handle deployment
        if missing_resources or existing_resources:
            if missing_resources:
                action_msg = f"Import {len(existing_resources)} existing + Create {len(missing_resources)} missing resources"
            else:
                action_msg = f"Import {len(existing_resources)} existing resources (no new resources needed)"
            
            proceed = input(f"\n{action_msg}? (y/N): ")
            if proceed.lower() != 'y':
                print_info("Deployment cancelled")
                return
            
            # Create import strategy
            create_terraform_import_script(existing_resources)
            
            # Run Terraform with imports
            if run_terraform_with_imports(existing_resources, missing_resources):
                print_status("🎉 Infrastructure deployment successful!")
                
                # Final verification
                print_info("Performing final verification...")
                final_existing, final_missing = comprehensive_aws_scan()
                
                if len(final_missing) == 0:
                    print_status("✅ ALL infrastructure is now properly deployed!")
                else:
                    print_warning(f"⚠️ Still missing {len(final_missing)} resources:")
                    for key, resource in final_missing.items():
                        print_warning(f"  • {resource['name']}")
            else:
                print_error("❌ Infrastructure deployment failed")
        else:
            print_status("✅ No infrastructure found - starting fresh deployment")
        
        # Step 5: Next steps
        print_title("Next Steps")
        configured_services = sum(1 for configured in services.values() if configured)
        total_services = len(services)
        
        if configured_services == total_services:
            print_status("All third-party services configured")
        else:
            print_warning(f"Configure remaining services: {total_services - configured_services} unconfigured")
        
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
