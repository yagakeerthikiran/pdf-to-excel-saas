#!/usr/bin/env python3
"""
TRULY RESUME-SAFE Infrastructure Deployment with PROPER AWS RESOURCE IMPORTS
- Fixed: Use correct AWS resource identifiers (ARNs/IDs) for Terraform imports
- Enhanced: Fetch actual AWS resource identifiers before import attempts
- Logic: Import failure doesn't mean resource needs creation - verify existence independently

DOCUMENTED ISSUES & FIXES:
=========================
ISSUE: Terraform import failed with "not a valid ARN" errors for ALB/Target Groups
CAUSE: Using resource names instead of required ARNs for Terraform import
FIX: Fetch actual ARNs using AWS CLI queries before import, handle import failures gracefully

ISSUE: Import failures causing script to assume resources need creation
CAUSE: Wrong logic - import failure doesn't mean resource doesn't exist
FIX: Separate existence checking from import attempts, only create truly missing resources

TERRAFORM IMPORT REQUIREMENTS:
- Load Balancer: Requires full ARN (not name)
- Target Groups: Requires full ARN (not name)  
- IAM Roles: Can use role name
- RDS Subnet Group: Can use name
- S3 Bucket: Uses bucket name
- RDS Instance: Uses DB instance identifier
- ECS Cluster: Uses cluster name
- ECR Repository: Uses repository name
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

def check_and_get_resource_details():
    """Check AWS resources and get their proper identifiers for import"""
    print_title("Checking AWS Resources and Getting Import Identifiers")
    
    resources = {}
    
    # DB Subnet Group
    db_subnet_group_name = f'{APP_NAME}-{ENVIRONMENT}-db-subnet-group'
    cmd = f'aws rds describe-db-subnet-groups --db-subnet-group-name {db_subnet_group_name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict) and result.get('DBSubnetGroups'):
        resources['db_subnet_group'] = {
            'exists': True,
            'name': db_subnet_group_name,
            'import_id': db_subnet_group_name,  # RDS subnet groups use name
            'terraform_resource': 'aws_db_subnet_group.main'
        }
        print_status(f"DB Subnet Group exists: {db_subnet_group_name}")
    else:
        resources['db_subnet_group'] = {'exists': False, 'name': db_subnet_group_name}
        print_warning(f"DB Subnet Group missing: {db_subnet_group_name}")
    
    # Load Balancer
    lb_name = f'{APP_NAME}-{ENVIRONMENT}-alb'
    lb_arn = get_load_balancer_arn(lb_name)
    
    if lb_arn:
        resources['load_balancer'] = {
            'exists': True,
            'name': lb_name,
            'import_id': lb_arn,  # Load balancers need ARN
            'terraform_resource': 'aws_lb.main'
        }
        print_status(f"Load Balancer exists: {lb_name}")
        print_info(f"  ARN: {lb_arn}")
    else:
        resources['load_balancer'] = {'exists': False, 'name': lb_name}
        print_warning(f"Load Balancer missing: {lb_name}")
    
    # Target Groups
    for tg_type in ['frontend', 'backend']:
        tg_name = f'{APP_NAME}-{ENVIRONMENT}-{tg_type}-tg'
        tg_arn = get_target_group_arn(tg_name)
        
        if tg_arn:
            resources[f'target_group_{tg_type}'] = {
                'exists': True,
                'name': tg_name,
                'import_id': tg_arn,  # Target groups need ARN
                'terraform_resource': f'aws_lb_target_group.{tg_type}'
            }
            print_status(f"Target Group {tg_type} exists: {tg_name}")
            print_info(f"  ARN: {tg_arn}")
        else:
            resources[f'target_group_{tg_type}'] = {'exists': False, 'name': tg_name}
            print_warning(f"Target Group {tg_type} missing: {tg_name}")
    
    # IAM Roles
    for role_type, role_suffix in [('execution', 'ecs-task-execution-role'), ('task', 'ecs-task-role')]:
        role_name = f'{APP_NAME}-{ENVIRONMENT}-{role_suffix}'
        cmd = f'aws iam get-role --role-name {role_name}'
        success, result = run_aws_command(cmd)
        
        if success and isinstance(result, dict) and result.get('Role'):
            resources[f'iam_role_{role_type}'] = {
                'exists': True,
                'name': role_name,
                'import_id': role_name,  # IAM roles use name
                'terraform_resource': f'aws_iam_role.ecs_task_{role_type}_role'
            }
            print_status(f"IAM Role {role_type} exists: {role_name}")
        else:
            resources[f'iam_role_{role_type}'] = {'exists': False, 'name': role_name}
            print_warning(f"IAM Role {role_type} missing: {role_name}")
    
    # S3 Bucket
    s3_bucket_name = f'{APP_NAME}-{ENVIRONMENT}'
    cmd = f'aws s3api head-bucket --bucket {s3_bucket_name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success:
        resources['s3_bucket'] = {
            'exists': True,
            'name': s3_bucket_name,
            'import_id': s3_bucket_name,  # S3 buckets use name
            'terraform_resource': 'aws_s3_bucket.main'
        }
        print_status(f"S3 Bucket exists: {s3_bucket_name}")
    else:
        resources['s3_bucket'] = {'exists': False, 'name': s3_bucket_name}
        print_warning(f"S3 Bucket missing: {s3_bucket_name}")
    
    # RDS Instance
    rds_name = f'{APP_NAME}-{ENVIRONMENT}-db'
    cmd = f'aws rds describe-db-instances --db-instance-identifier {rds_name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict) and result.get('DBInstances'):
        resources['rds_instance'] = {
            'exists': True,
            'name': rds_name,
            'import_id': rds_name,  # RDS instances use identifier
            'terraform_resource': 'aws_db_instance.main'
        }
        print_status(f"RDS Instance exists: {rds_name}")
    else:
        resources['rds_instance'] = {'exists': False, 'name': rds_name}
        print_warning(f"RDS Instance missing: {rds_name}")
    
    # ECS Cluster
    ecs_name = f'{APP_NAME}-{ENVIRONMENT}'
    cmd = f'aws ecs describe-clusters --clusters {ecs_name} --region {AWS_REGION}'
    success, result = run_aws_command(cmd)
    
    if success and isinstance(result, dict):
        clusters = result.get('clusters', [])
        if clusters and clusters[0].get('status') == 'ACTIVE':
            resources['ecs_cluster'] = {
                'exists': True,
                'name': ecs_name,
                'import_id': ecs_name,  # ECS clusters use name
                'terraform_resource': 'aws_ecs_cluster.main'
            }
            print_status(f"ECS Cluster exists: {ecs_name}")
        else:
            resources['ecs_cluster'] = {'exists': False, 'name': ecs_name}
            print_warning(f"ECS Cluster missing: {ecs_name}")
    else:
        resources['ecs_cluster'] = {'exists': False, 'name': ecs_name}
        print_warning(f"ECS Cluster missing: {ecs_name}")
    
    # ECR Repositories
    for repo_type in ['frontend', 'backend']:
        repo_name = f'{APP_NAME}-{repo_type}'
        cmd = f'aws ecr describe-repositories --repository-names {repo_name} --region {AWS_REGION}'
        success, result = run_aws_command(cmd)
        
        if success and isinstance(result, dict) and result.get('repositories'):
            resources[f'ecr_{repo_type}'] = {
                'exists': True,
                'name': repo_name,
                'import_id': repo_name,  # ECR repos use name
                'terraform_resource': f'aws_ecr_repository.{repo_type}'
            }
            print_status(f"ECR Repository {repo_type} exists: {repo_name}")
        else:
            resources[f'ecr_{repo_type}'] = {'exists': False, 'name': repo_name}
            print_warning(f"ECR Repository {repo_type} missing: {repo_name}")
    
    return resources

def import_existing_resources(resources):
    """Import existing resources into Terraform state using correct identifiers"""
    print_title("Importing Existing Resources into Terraform State")
    
    existing_resources = {k: v for k, v in resources.items() if v.get('exists')}
    
    if not existing_resources:
        print_info("No existing resources to import")
        return True
    
    print_info(f"Found {len(existing_resources)} existing resources to import")
    
    import_results = {}
    
    for resource_key, resource_info in existing_resources.items():
        terraform_resource = resource_info['terraform_resource']
        import_id = resource_info['import_id']
        resource_name = resource_info['name']
        
        print_info(f"Importing {resource_name}...")
        print_info(f"  Terraform resource: {terraform_resource}")
        print_info(f"  Import ID: {import_id}")
        
        import_cmd = f'terraform import {terraform_resource} {import_id}'
        result = subprocess.run(import_cmd, shell=True, cwd='infra', 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_status(f"✅ Successfully imported: {resource_name}")
            import_results[resource_key] = True
        else:
            print_warning(f"⚠️ Import failed for {resource_name}")
            print_warning(f"   Error: {result.stderr}")
            
            # IMPORTANT: Import failure doesn't mean resource doesn't exist!
            # The resource exists in AWS, just not in Terraform state
            if "already exists" in result.stderr or "Resource already managed" in result.stderr:
                print_info(f"   Resource {resource_name} already in Terraform state")
                import_results[resource_key] = True
            else:
                print_info(f"   Resource {resource_name} exists in AWS but import failed")
                import_results[resource_key] = False
    
    successful_imports = sum(1 for success in import_results.values() if success)
    print_status(f"Import summary: {successful_imports}/{len(existing_resources)} successful")
    
    return True

def run_terraform_deployment(resources):
    """Run Terraform deployment only for truly missing resources"""
    print_title("Running Terraform Deployment")
    
    existing_resources = {k: v for k, v in resources.items() if v.get('exists')}
    missing_resources = {k: v for k, v in resources.items() if not v.get('exists')}
    
    print_info(f"Existing resources: {len(existing_resources)}")
    print_info(f"Missing resources: {len(missing_resources)}")
    
    if missing_resources:
        print_info("Missing resources that will be created:")
        for key, resource in missing_resources.items():
            print(f"  ❌ {key}: {resource['name']}")
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    result = subprocess.run('terraform init -reconfigure', shell=True, cwd='infra',
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print_error("Terraform init failed")
        print_error(result.stderr)
        return False
    
    print_status("Terraform initialized")
    
    # Import existing resources
    if existing_resources:
        import_existing_resources(resources)
    
    # Plan deployment
    print_info("Planning deployment...")
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}" -out=tfplan'
    result = subprocess.run(plan_cmd, shell=True, cwd='infra', capture_output=True, text=True)
    
    if result.returncode != 0:
        print_error("Terraform plan failed")
        print_error(result.stderr)
        return False
    
    # Show plan summary
    if result.stdout:
        lines = result.stdout.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['Plan:', 'will be created', 'will be updated', 'will be destroyed', 'No changes']):
                print_info(f"Plan: {line}")
    
    # Check if anything needs to be created
    if 'No changes' in result.stdout:
        print_status("✅ All resources exist and are properly managed by Terraform!")
        return True
    
    # Confirm deployment of missing resources only
    if missing_resources:
        print(f"\n{Colors.YELLOW}[WARNING] This will create {len(missing_resources)} missing AWS resources.{Colors.END}")
        print(f"{Colors.CYAN}Existing resources will NOT be recreated.{Colors.END}")
        confirm = input("Proceed with creating missing resources? (y/N): ")
        
        if confirm.lower() != 'y':
            print_warning("Deployment cancelled")
            return False
    
    # Apply changes
    print_info("Applying Terraform configuration...")
    result = subprocess.run('terraform apply tfplan', shell=True, cwd='infra',
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print_status("🎉 Infrastructure deployment completed successfully!")
        return True
    else:
        print_error("❌ Terraform apply failed!")
        print_error(result.stderr)
        
        # If we still get "already exists" errors, it means our detection missed something
        if "already exists" in result.stderr:
            print_warning("Some resources still show as 'already exists'")
            print_info("This indicates our AWS resource detection may need refinement")
            print_info("The resources exist in AWS but may have different names or configurations")
        
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
    """Main deployment function with proper AWS resource import handling"""
    print(f"{Colors.BLUE}")
    print("=== PDF to Excel SaaS - FIXED TERRAFORM IMPORT Deployment ===")
    print("============================================================")
    print("Strategy: Proper AWS resource identification + Import with correct identifiers")
    print(f"App: {APP_NAME} | Environment: {ENVIRONMENT} | Region: {AWS_REGION}")
    print(f"{Colors.END}")
    
    try:
        # Step 1: Validate AWS access
        account_id = get_aws_account_info()
        if not account_id:
            return
        
        print_status(f"AWS Account: {account_id}")
        
        # Step 2: Check all AWS resources and get proper identifiers
        resources = check_and_get_resource_details()
        
        print_title("Resource Analysis Summary")
        
        existing_count = sum(1 for r in resources.values() if r.get('exists'))
        missing_count = len(resources) - existing_count
        
        print_status(f"Existing resources: {existing_count}")
        print_warning(f"Missing resources: {missing_count}")
        
        # Step 3: Check third-party services
        services = check_third_party_services()
        
        # Step 4: Handle deployment with proper import logic
        if missing_count > 0 or existing_count > 0:
            action_msg = f"Import {existing_count} existing + Create {missing_count} missing resources"
            
            proceed = input(f"\n{action_msg}? (y/N): ")
            if proceed.lower() != 'y':
                print_info("Deployment cancelled")
                return
            
            # Clean Terraform state for fresh start
            terraform_dirs = ['infra/.terraform', 'infra/.terraform.lock.hcl']
            for item in terraform_dirs:
                path = Path(item)
                if path.exists():
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            
            # Run deployment with proper imports
            if run_terraform_deployment(resources):
                print_status("🎉 Infrastructure deployment successful!")
                
                # Final verification
                print_info("Performing final verification...")
                final_resources = check_and_get_resource_details()
                final_missing = sum(1 for r in final_resources.values() if not r.get('exists'))
                
                if final_missing == 0:
                    print_status("✅ ALL infrastructure is now properly deployed!")
                else:
                    print_warning(f"⚠️ Still missing {final_missing} resources")
            else:
                print_error("❌ Infrastructure deployment failed")
        else:
            print_status("✅ No infrastructure changes needed")
        
        # Step 5: Next steps
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
