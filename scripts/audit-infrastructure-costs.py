#!/usr/bin/env python3
"""
AWS Infrastructure Cost Audit Script
- Shows exactly what exists in AWS vs Terraform state
- Identifies potential duplicate resources and costs
- Provides safe cleanup recommendations
- Prevents accidental expensive resource creation
"""

import subprocess
import json
import sys
import boto3
from pathlib import Path
from typing import Dict, List, Tuple

AWS_REGION = "ap-southeast-2"
APP_NAME = "pdf-excel-saas"
ENVIRONMENT = "prod"

# AWS resource costs (monthly estimates in USD)
RESOURCE_COSTS = {
    'rds_db_instance': {'db.t3.micro': 15, 'db.t3.small': 30, 'db.t3.medium': 60},
    'nat_gateway': 45,
    'load_balancer': 20,
    'ecs_cluster': 0,  # Free tier
    'ecr_repository': 1,  # Per GB stored
    's3_bucket': 5,  # Estimate
    'iam_role': 0,
    'security_group': 0,
    'vpc': 0,
    'subnet': 0
}

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    END = '\033[0m'

def print_status(msg): 
    print(f"{Colors.GREEN}[SUCCESS] {msg}{Colors.END}")

def print_warning(msg): 
    print(f"{Colors.YELLOW}[WARNING] {msg}{Colors.END}")

def print_error(msg): 
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_info(msg): 
    print(f"{Colors.CYAN}[INFO] {msg}{Colors.END}")

def print_cost(msg): 
    print(f"{Colors.PURPLE}[COST] {msg}{Colors.END}")

def print_title(msg):
    print(f"\n{Colors.BLUE}=== {msg} ==={Colors.END}")
    print("=" * (len(msg) + 8))

def run_command(cmd, cwd=None) -> Tuple[bool, str, str]:
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_aws_session() -> boto3.Session:
    """Get configured AWS session"""
    return boto3.Session(region_name=AWS_REGION)

def check_aws_credentials() -> Tuple[bool, str]:
    """Verify AWS credentials"""
    try:
        session = get_aws_session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        print_status(f"AWS Account: {account_id} | Region: {AWS_REGION}")
        return True, account_id
    except Exception as e:
        print_error(f"AWS credentials not configured: {e}")
        return False, None

def audit_expensive_resources(session: boto3.Session) -> Dict:
    """Audit expensive AWS resources to prevent duplicates"""
    print_title("Auditing Expensive AWS Resources")
    
    expensive_resources = {
        'rds_instances': [],
        'nat_gateways': [],
        'load_balancers': [],
        'ecs_clusters': [],
        'ecr_repositories': [],
        's3_buckets': []
    }
    
    total_estimated_cost = 0
    
    # RDS Instances (EXPENSIVE)
    print_info("Checking RDS instances...")
    rds = session.client('rds')
    try:
        rds_instances = rds.describe_db_instances()['DBInstances']
        for db in rds_instances:
            db_id = db['DBInstanceIdentifier']
            db_class = db['DBInstanceClass']
            db_status = db['DBInstanceStatus']
            
            if APP_NAME in db_id or ENVIRONMENT in db_id:
                cost = RESOURCE_COSTS['rds_db_instance'].get(db_class, 30)
                total_estimated_cost += cost
                
                expensive_resources['rds_instances'].append({
                    'id': db_id,
                    'class': db_class,
                    'status': db_status,
                    'cost': cost
                })
                
                print_cost(f"RDS: {db_id} ({db_class}) - ${cost}/month - Status: {db_status}")
                
    except Exception as e:
        print_warning(f"Could not check RDS: {e}")
    
    # NAT Gateways (EXPENSIVE)
    print_info("Checking NAT Gateways...")
    ec2 = session.client('ec2')
    try:
        nat_gateways = ec2.describe_nat_gateways()['NatGateways']
        for nat in nat_gateways:
            if nat['State'] in ['available', 'pending']:
                nat_id = nat['NatGatewayId']
                
                # Check if it's ours by checking tags or associated resources
                tags = nat.get('Tags', [])
                is_ours = any(APP_NAME in tag.get('Value', '').lower() for tag in tags)
                
                if is_ours:
                    cost = RESOURCE_COSTS['nat_gateway']
                    total_estimated_cost += cost
                    
                    expensive_resources['nat_gateways'].append({
                        'id': nat_id,
                        'state': nat['State'],
                        'cost': cost
                    })
                    
                    print_cost(f"NAT Gateway: {nat_id} - ${cost}/month - State: {nat['State']}")
                    
    except Exception as e:
        print_warning(f"Could not check NAT Gateways: {e}")
    
    # Load Balancers (MODERATE COST)
    print_info("Checking Load Balancers...")
    elbv2 = session.client('elbv2')
    try:
        load_balancers = elbv2.describe_load_balancers()['LoadBalancers']
        for lb in load_balancers:
            lb_name = lb['LoadBalancerName']
            lb_state = lb['State']['Code']
            
            if APP_NAME in lb_name:
                cost = RESOURCE_COSTS['load_balancer']
                total_estimated_cost += cost
                
                expensive_resources['load_balancers'].append({
                    'name': lb_name,
                    'arn': lb['LoadBalancerArn'],
                    'state': lb_state,
                    'cost': cost
                })
                
                print_cost(f"Load Balancer: {lb_name} - ${cost}/month - State: {lb_state}")
                
    except Exception as e:
        print_warning(f"Could not check Load Balancers: {e}")
    
    # ECS Clusters (FREE)
    print_info("Checking ECS Clusters...")
    ecs = session.client('ecs')
    try:
        cluster_arns = ecs.list_clusters()['clusterArns']
        if cluster_arns:
            clusters = ecs.describe_clusters(clusters=cluster_arns)['clusters']
            for cluster in clusters:
                cluster_name = cluster['clusterName']
                if APP_NAME in cluster_name:
                    expensive_resources['ecs_clusters'].append({
                        'name': cluster_name,
                        'status': cluster['status'],
                        'cost': 0
                    })
                    print_info(f"ECS Cluster: {cluster_name} - FREE - Status: {cluster['status']}")
                    
    except Exception as e:
        print_warning(f"Could not check ECS Clusters: {e}")
    
    # ECR Repositories (LOW COST)
    print_info("Checking ECR Repositories...")
    ecr = session.client('ecr')
    try:
        repositories = ecr.describe_repositories()['repositories']
        for repo in repositories:
            repo_name = repo['repositoryName']
            if APP_NAME in repo_name:
                expensive_resources['ecr_repositories'].append({
                    'name': repo_name,
                    'uri': repo['repositoryUri'],
                    'cost': 1
                })
                print_info(f"ECR Repository: {repo_name} - ~$1/month")
                
    except Exception as e:
        print_warning(f"Could not check ECR Repositories: {e}")
    
    # S3 Buckets (LOW COST)
    print_info("Checking S3 Buckets...")
    s3 = session.client('s3')
    try:
        buckets = s3.list_buckets()['Buckets']
        for bucket in buckets:
            bucket_name = bucket['Name']
            if APP_NAME in bucket_name:
                expensive_resources['s3_buckets'].append({
                    'name': bucket_name,
                    'cost': 5
                })
                total_estimated_cost += 5
                print_info(f"S3 Bucket: {bucket_name} - ~$5/month")
                
    except Exception as e:
        print_warning(f"Could not check S3 Buckets: {e}")
    
    print_cost(f"\nTotal Estimated Monthly Cost: ${total_estimated_cost}")
    
    return expensive_resources

def get_terraform_plan_details() -> Dict:
    """Get detailed Terraform plan to see what would be created/destroyed"""
    print_title("Analyzing Terraform Plan")
    
    # Initialize Terraform
    success, stdout, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print_error(f"Terraform init failed: {stderr}")
        return {}
    
    # Generate plan
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(plan_cmd, cwd='infra')
    
    plan_details = {
        'to_add': [],
        'to_change': [],
        'to_destroy': [],
        'blocked_by_lifecycle': []
    }
    
    if success:
        lines = stdout.split('\n')
        current_resource = None
        
        for line in lines:
            line = line.strip()
            
            if '# aws_' in line and 'will be created' in line:
                resource = line.split('#')[1].split('will be created')[0].strip()
                plan_details['to_add'].append(resource)
                
            elif '# aws_' in line and 'will be destroyed' in line:
                resource = line.split('#')[1].split('will be destroyed')[0].strip()
                plan_details['to_destroy'].append(resource)
                
            elif '# aws_' in line and 'must be replaced' in line:
                resource = line.split('#')[1].split('must be replaced')[0].strip()
                plan_details['to_destroy'].append(resource)
                plan_details['to_add'].append(resource)
                
            elif 'Plan:' in line:
                print_info(f"Terraform Plan Summary: {line}")
                
    elif "lifecycle.prevent_destroy" in stderr:
        print_warning("Plan blocked by lifecycle protection")
        plan_details['blocked_by_lifecycle'] = ['Target groups and other protected resources']
    else:
        print_error(f"Plan failed: {stderr}")
    
    return plan_details

def analyze_potential_duplicates(aws_resources: Dict, plan_details: Dict):
    """Analyze if we might create duplicate expensive resources"""
    print_title("Duplicate Resource Analysis")
    
    # Check for potential RDS duplicates
    existing_rds = len(aws_resources.get('rds_instances', []))
    planned_rds = sum(1 for r in plan_details.get('to_add', []) if 'aws_db_instance' in r)
    
    if existing_rds > 0 and planned_rds > 0:
        print_error(f"DUPLICATE RISK: {existing_rds} RDS instance(s) exist, plan wants to create {planned_rds} more!")
        print_cost(f"Potential cost: +${planned_rds * 30}/month")
    
    # Check for potential NAT Gateway duplicates
    existing_nat = len(aws_resources.get('nat_gateways', []))
    planned_nat = sum(1 for r in plan_details.get('to_add', []) if 'aws_nat_gateway' in r)
    
    if existing_nat > 0 and planned_nat > 0:
        print_error(f"DUPLICATE RISK: {existing_nat} NAT Gateway(s) exist, plan wants to create {planned_nat} more!")
        print_cost(f"Potential cost: +${planned_nat * 45}/month")
    
    # Check for potential Load Balancer duplicates
    existing_lb = len(aws_resources.get('load_balancers', []))
    planned_lb = sum(1 for r in plan_details.get('to_add', []) if 'aws_lb.' in r and 'target_group' not in r)
    
    if existing_lb > 0 and planned_lb > 0:
        print_error(f"DUPLICATE RISK: {existing_lb} Load Balancer(s) exist, plan wants to create {planned_lb} more!")
        print_cost(f"Potential cost: +${planned_lb * 20}/month")

def provide_safe_recommendations(aws_resources: Dict, plan_details: Dict):
    """Provide safe recommendations to avoid duplicates"""
    print_title("Safe Deployment Recommendations")
    
    has_expensive_resources = (
        len(aws_resources.get('rds_instances', [])) > 0 or
        len(aws_resources.get('nat_gateways', [])) > 0 or
        len(aws_resources.get('load_balancers', [])) > 0
    )
    
    if has_expensive_resources:
        print_warning("You have existing expensive resources. Recommendations:")
        print_info("1. 🛑 STOP - Do not run terraform apply yet")
        print_info("2. 🔍 Use terraform import to bring existing resources into state")
        print_info("3. 🧹 Clean up Terraform state duplicates first")
        print_info("4. 🎯 Use targeted applies for specific resources only")
        
        print_info("\nSafe import commands:")
        
        for rds in aws_resources.get('rds_instances', []):
            print_info(f"   terraform import aws_db_instance.main {rds['id']}")
        
        for nat in aws_resources.get('nat_gateways', []):
            print_info(f"   # NAT Gateway: {nat['id']} (check if this matches expected resources)")
            
        print_info("\n⚠️  Before any terraform apply:")
        print_info("   - Verify imports with 'terraform plan'")
        print_info("   - Ensure plan shows 0 to add for expensive resources")
        print_info("   - Use 'terraform state list' to verify state")
        
    else:
        print_status("No expensive resources found - safe to proceed with deployment")

def main():
    """Main audit function"""
    print(f"{Colors.BLUE}")
    print("=== AWS INFRASTRUCTURE COST AUDIT ===")
    print("=====================================")
    print("Preventing accidental duplicate resource creation")
    print(f"Region: {AWS_REGION} | Environment: {ENVIRONMENT}")
    print(f"{Colors.END}")
    
    # Check AWS credentials
    creds_ok, account_id = check_aws_credentials()
    if not creds_ok:
        sys.exit(1)
    
    if not Path('infra/main.tf').exists():
        print_error("Terraform configuration not found")
        sys.exit(1)
    
    try:
        # Get AWS session
        session = get_aws_session()
        
        # Audit expensive resources
        aws_resources = audit_expensive_resources(session)
        
        # Get Terraform plan details
        plan_details = get_terraform_plan_details()
        
        # Analyze potential duplicates
        analyze_potential_duplicates(aws_resources, plan_details)
        
        # Provide safe recommendations
        provide_safe_recommendations(aws_resources, plan_details)
        
        print_title("Summary")
        print_info("✅ Cost audit completed")
        print_info("✅ Duplicate risk analysis done")
        print_info("✅ Safe recommendations provided")
        
    except Exception as e:
        print_error(f"Audit failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
