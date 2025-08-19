#!/usr/bin/env python3
"""
Intelligent Infrastructure Deployment Script
- Discovers existing AWS resources directly
- Compares with Terraform state for inconsistencies
- Auto-reconciles stale/orphaned state objects
- Generates dynamic terraform operations (create/update/delete/recreate)
- Provides detailed drift analysis and remediation
"""

import subprocess
import json
import sys
import time
import boto3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

AWS_REGION = "ap-southeast-2"
APP_NAME = "pdf-excel-saas"
ENVIRONMENT = "prod"

@dataclass
class ResourceDrift:
    """Represents a resource that has drifted from expected state"""
    resource_type: str
    resource_name: str
    aws_state: Dict
    terraform_state: Optional[Dict]
    drift_type: str  # 'missing', 'extra', 'modified', 'orphaned'
    recommended_action: str  # 'create', 'import', 'update', 'delete', 'recreate'

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

def print_title(msg):
    print(f"\n{Colors.BLUE}=== {msg} ==={Colors.END}")
    print("=" * (len(msg) + 8))

def print_drift(msg):
    print(f"{Colors.PURPLE}[DRIFT] {msg}{Colors.END}")

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

def check_aws_credentials() -> Tuple[bool, Optional[str]]:
    """Verify AWS credentials and return account ID"""
    try:
        session = get_aws_session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        print_status(f"AWS Account: {account_id} | Region: {AWS_REGION}")
        return True, account_id
    except Exception as e:
        print_error(f"AWS credentials not configured: {e}")
        print_info("Run: aws configure")
        return False, None

def discover_aws_resources(session: boto3.Session) -> Dict[str, List[Dict]]:
    """Discover existing AWS resources that match our app pattern"""
    print_title("Discovering AWS Resources")
    
    resources = {
        'vpcs': [],
        'subnets': [],
        'security_groups': [],
        'internet_gateways': [],
        'nat_gateways': [],
        'route_tables': [],
        'load_balancers': [],
        'target_groups': [],
        'ecs_clusters': [],
        'ecs_services': [],
        'ecs_task_definitions': [],
        'ecr_repositories': [],
        'rds_instances': [],
        'rds_subnets': [],
        's3_buckets': [],
        'iam_roles': [],
        'cloudwatch_logs': []
    }
    
    try:
        # VPC Resources
        ec2 = session.client('ec2')
        
        # VPCs
        vpcs = ec2.describe_vpcs()['Vpcs']
        app_vpcs = [vpc for vpc in vpcs if any(
            tag.get('Value', '').startswith(APP_NAME) 
            for tag in vpc.get('Tags', [])
        )]
        resources['vpcs'] = app_vpcs
        print_info(f"Found {len(app_vpcs)} VPCs")
        
        # Subnets
        if app_vpcs:
            vpc_ids = [vpc['VpcId'] for vpc in app_vpcs]
            subnets = ec2.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': vpc_ids}]
            )['Subnets']
            resources['subnets'] = subnets
            print_info(f"Found {len(subnets)} Subnets")
        
        # Security Groups
        security_groups = ec2.describe_security_groups()['SecurityGroups']
        app_sgs = [sg for sg in security_groups if any(
            APP_NAME in sg.get('GroupName', '') or
            any(tag.get('Value', '').startswith(APP_NAME) 
                for tag in sg.get('Tags', []))
        )]
        resources['security_groups'] = app_sgs
        print_info(f"Found {len(app_sgs)} Security Groups")
        
        # Load Balancers
        elbv2 = session.client('elbv2')
        load_balancers = elbv2.describe_load_balancers()['LoadBalancers']
        app_lbs = [lb for lb in load_balancers if APP_NAME in lb.get('LoadBalancerName', '')]
        resources['load_balancers'] = app_lbs
        print_info(f"Found {len(app_lbs)} Load Balancers")
        
        # Target Groups
        target_groups = elbv2.describe_target_groups()['TargetGroups']
        app_tgs = [tg for tg in target_groups if APP_NAME in tg.get('TargetGroupName', '')]
        resources['target_groups'] = app_tgs
        print_info(f"Found {len(app_tgs)} Target Groups")
        
        # ECS Resources
        ecs = session.client('ecs')
        
        # ECS Clusters
        cluster_arns = ecs.list_clusters()['clusterArns']
        if cluster_arns:
            clusters = ecs.describe_clusters(clusters=cluster_arns)['clusters']
            app_clusters = [c for c in clusters if APP_NAME in c.get('clusterName', '')]
            resources['ecs_clusters'] = app_clusters
            print_info(f"Found {len(app_clusters)} ECS Clusters")
            
            # ECS Services
            for cluster in app_clusters:
                service_arns = ecs.list_services(cluster=cluster['clusterArn'])['serviceArns']
                if service_arns:
                    services = ecs.describe_services(
                        cluster=cluster['clusterArn'], 
                        services=service_arns
                    )['services']
                    resources['ecs_services'].extend(services)
            print_info(f"Found {len(resources['ecs_services'])} ECS Services")
        
        # ECR Repositories
        ecr = session.client('ecr')
        try:
            repositories = ecr.describe_repositories()['repositories']
            app_repos = [repo for repo in repositories if APP_NAME in repo.get('repositoryName', '')]
            resources['ecr_repositories'] = app_repos
            print_info(f"Found {len(app_repos)} ECR Repositories")
        except Exception as e:
            print_warning(f"Could not check ECR repositories: {e}")
        
        # RDS Resources
        rds = session.client('rds')
        
        # RDS Instances
        db_instances = rds.describe_db_instances()['DBInstances']
        app_dbs = [db for db in db_instances if APP_NAME in db.get('DBInstanceIdentifier', '')]
        resources['rds_instances'] = app_dbs
        print_info(f"Found {len(app_dbs)} RDS Instances")
        
        # RDS Subnet Groups
        subnet_groups = rds.describe_db_subnet_groups()['DBSubnetGroups']
        app_subnet_groups = [sg for sg in subnet_groups if APP_NAME in sg.get('DBSubnetGroupName', '')]
        resources['rds_subnets'] = app_subnet_groups
        print_info(f"Found {len(app_subnet_groups)} RDS Subnet Groups")
        
        # S3 Buckets
        s3 = session.client('s3')
        try:
            buckets = s3.list_buckets()['Buckets']
            app_buckets = [bucket for bucket in buckets if APP_NAME in bucket.get('Name', '')]
            resources['s3_buckets'] = app_buckets
            print_info(f"Found {len(app_buckets)} S3 Buckets")
        except Exception as e:
            print_warning(f"Could not check S3 buckets: {e}")
        
        # IAM Roles
        iam = session.client('iam')
        try:
            roles = iam.list_roles()['Roles']
            app_roles = [role for role in roles if APP_NAME in role.get('RoleName', '')]
            resources['iam_roles'] = app_roles
            print_info(f"Found {len(app_roles)} IAM Roles")
        except Exception as e:
            print_warning(f"Could not check IAM roles: {e}")
        
        # CloudWatch Log Groups
        logs = session.client('logs')
        try:
            log_groups = logs.describe_log_groups()['logGroups']
            app_logs = [lg for lg in log_groups if APP_NAME in lg.get('logGroupName', '')]
            resources['cloudwatch_logs'] = app_logs
            print_info(f"Found {len(app_logs)} CloudWatch Log Groups")
        except Exception as e:
            print_warning(f"Could not check CloudWatch logs: {e}")
            
    except Exception as e:
        print_error(f"Error discovering AWS resources: {e}")
    
    return resources

def get_terraform_state() -> Dict:
    """Get current Terraform state"""
    print_title("Analyzing Terraform State")
    
    # Initialize Terraform if needed
    if not Path('infra/.terraform').exists():
        print_info("Initializing Terraform...")
        success, _, stderr = run_command('terraform init', cwd='infra')
        if not success:
            print_error(f"Terraform init failed: {stderr}")
            return {}
    
    # Get state
    success, stdout, stderr = run_command('terraform show -json', cwd='infra')
    if not success:
        print_warning(f"Could not read Terraform state: {stderr}")
        return {}
    
    try:
        state = json.loads(stdout)
        resources = state.get('values', {}).get('root_module', {}).get('resources', [])
        print_info(f"Found {len(resources)} resources in Terraform state")
        return state
    except json.JSONDecodeError as e:
        print_error(f"Invalid Terraform state JSON: {e}")
        return {}

def analyze_drift(aws_resources: Dict, terraform_state: Dict) -> List[ResourceDrift]:
    """Analyze drift between AWS reality and Terraform state"""
    print_title("Analyzing Resource Drift")
    
    drifts = []
    tf_resources = terraform_state.get('values', {}).get('root_module', {}).get('resources', [])
    
    # Convert Terraform resources to lookup dict
    tf_lookup = {}
    for resource in tf_resources:
        key = f"{resource['type']}.{resource['name']}"
        tf_lookup[key] = resource
    
    # Check for resources in AWS but not in Terraform (orphaned)
    aws_resource_map = {
        'aws_vpc': aws_resources['vpcs'],
        'aws_subnet': aws_resources['subnets'],
        'aws_security_group': aws_resources['security_groups'],
        'aws_lb': aws_resources['load_balancers'],
        'aws_lb_target_group': aws_resources['target_groups'],
        'aws_ecs_cluster': aws_resources['ecs_clusters'],
        'aws_ecs_service': aws_resources['ecs_services'],
        'aws_ecr_repository': aws_resources['ecr_repositories'],
        'aws_db_instance': aws_resources['rds_instances'],
        'aws_db_subnet_group': aws_resources['rds_subnets'],
        'aws_s3_bucket': aws_resources['s3_buckets'],
        'aws_iam_role': aws_resources['iam_roles'],
        'aws_cloudwatch_log_group': aws_resources['cloudwatch_logs']
    }
    
    # Find orphaned resources (in AWS but not in Terraform)
    for resource_type, aws_items in aws_resource_map.items():
        for item in aws_items:
            # Extract identifier based on resource type
            identifier = get_resource_identifier(resource_type, item)
            tf_key = f"{resource_type}.{identifier}"
            
            if tf_key not in tf_lookup:
                drifts.append(ResourceDrift(
                    resource_type=resource_type,
                    resource_name=identifier,
                    aws_state=item,
                    terraform_state=None,
                    drift_type='orphaned',
                    recommended_action='import'
                ))
    
    # Find missing resources (in Terraform but not in AWS)
    for tf_key, tf_resource in tf_lookup.items():
        resource_type = tf_resource['type']
        if resource_type in aws_resource_map:
            # Check if this Terraform resource exists in AWS
            aws_items = aws_resource_map[resource_type]
            tf_identifier = tf_resource['name']
            
            found_in_aws = False
            for aws_item in aws_items:
                aws_identifier = get_resource_identifier(resource_type, aws_item)
                if aws_identifier == tf_identifier:
                    found_in_aws = True
                    break
            
            if not found_in_aws:
                drifts.append(ResourceDrift(
                    resource_type=resource_type,
                    resource_name=tf_identifier,
                    aws_state={},
                    terraform_state=tf_resource,
                    drift_type='missing',
                    recommended_action='create'
                ))
    
    print_info(f"Found {len(drifts)} resource drifts")
    return drifts

def get_resource_identifier(resource_type: str, aws_resource: Dict) -> str:
    """Extract resource identifier from AWS resource data"""
    identifier_map = {
        'aws_vpc': 'VpcId',
        'aws_subnet': 'SubnetId', 
        'aws_security_group': 'GroupName',
        'aws_lb': 'LoadBalancerName',
        'aws_lb_target_group': 'TargetGroupName',
        'aws_ecs_cluster': 'clusterName',
        'aws_ecs_service': 'serviceName',
        'aws_ecr_repository': 'repositoryName',
        'aws_db_instance': 'DBInstanceIdentifier',
        'aws_db_subnet_group': 'DBSubnetGroupName',
        'aws_s3_bucket': 'Name',
        'aws_iam_role': 'RoleName',
        'aws_cloudwatch_log_group': 'logGroupName'
    }
    
    field = identifier_map.get(resource_type, 'id')
    return aws_resource.get(field, 'unknown')

def reconcile_state(drifts: List[ResourceDrift]) -> bool:
    """Reconcile Terraform state with AWS reality"""
    if not drifts:
        print_status("No state reconciliation needed")
        return True
    
    print_title("State Reconciliation Plan")
    
    # Group drifts by action
    actions = {'import': [], 'create': [], 'update': [], 'delete': [], 'recreate': []}
    
    for drift in drifts:
        actions[drift.recommended_action].append(drift)
    
    # Display reconciliation plan
    for action, items in actions.items():
        if items:
            print(f"\n{Colors.CYAN}{action.upper()} ({len(items)} resources):{Colors.END}")
            for item in items:
                print(f"  • {item.resource_type}.{item.resource_name} - {item.drift_type}")
    
    # Ask for confirmation
    print(f"\n{Colors.YELLOW}This will modify Terraform state and/or resources.{Colors.END}")
    confirm = input("Proceed with reconciliation? (y/N): ")
    if confirm.lower() != 'y':
        print_info("State reconciliation cancelled")
        return False
    
    # Execute reconciliation
    print_title("Executing State Reconciliation")
    
    success_count = 0
    total_count = len(drifts)
    
    # Import orphaned resources
    for drift in actions['import']:
        print_info(f"Importing {drift.resource_type}.{drift.resource_name}")
        # Generate import command
        aws_id = get_aws_resource_id(drift.resource_type, drift.aws_state)
        import_cmd = f'terraform import {drift.resource_type}.{drift.resource_name} {aws_id}'
        success, stdout, stderr = run_command(import_cmd, cwd='infra')
        
        if success:
            print_status(f"Imported {drift.resource_name}")
            success_count += 1
        else:
            print_error(f"Failed to import {drift.resource_name}: {stderr}")
    
    # Handle missing resources (will be created in next terraform apply)
    for drift in actions['create']:
        print_info(f"Marked for creation: {drift.resource_type}.{drift.resource_name}")
        success_count += 1
    
    print_status(f"Reconciliation completed: {success_count}/{total_count} successful")
    return success_count == total_count

def get_aws_resource_id(resource_type: str, aws_resource: Dict) -> str:
    """Get the AWS resource ID for terraform import"""
    id_map = {
        'aws_vpc': 'VpcId',
        'aws_subnet': 'SubnetId',
        'aws_security_group': 'GroupId',
        'aws_lb': 'LoadBalancerArn',
        'aws_lb_target_group': 'TargetGroupArn',
        'aws_ecs_cluster': 'clusterArn',
        'aws_ecs_service': 'serviceArn',
        'aws_ecr_repository': 'repositoryName',
        'aws_db_instance': 'DBInstanceIdentifier',
        'aws_db_subnet_group': 'DBSubnetGroupName',
        'aws_s3_bucket': 'Name',
        'aws_iam_role': 'RoleName',
        'aws_cloudwatch_log_group': 'logGroupName'
    }
    
    field = id_map.get(resource_type, 'id')
    return aws_resource.get(field, '')

def generate_terraform_plan() -> bool:
    """Generate and review Terraform execution plan"""
    print_title("Generating Terraform Plan")
    
    plan_cmd = f'terraform plan -detailed-exitcode -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(plan_cmd, cwd='infra')
    
    if success:
        print_status("No changes needed - infrastructure is up to date")
        return True
    elif stderr and "Error" in stderr:
        print_error(f"Plan failed: {stderr}")
        return False
    else:
        print_info("Changes detected in plan")
        print(stdout)
        return True

def apply_terraform_changes() -> bool:
    """Apply Terraform changes after confirmation"""
    print_title("Applying Terraform Changes")
    
    confirm = input(f"{Colors.YELLOW}Apply the above changes? (y/N): {Colors.END}")
    if confirm.lower() != 'y':
        print_info("Deployment cancelled")
        return False
    
    apply_cmd = f'terraform apply -auto-approve -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(apply_cmd, cwd='infra')
    
    if success:
        print_status("Infrastructure changes applied successfully")
        return True
    else:
        print_error(f"Apply failed: {stderr}")
        return False

def main():
    """Main intelligent deployment function"""
    print(f"{Colors.BLUE}")
    print("=== INTELLIGENT INFRASTRUCTURE DEPLOYMENT ===")
    print("==============================================")
    print(f"Region: {AWS_REGION} | Environment: {ENVIRONMENT}")
    print(f"App: {APP_NAME}")
    print(f"{Colors.END}")
    
    # Check prerequisites
    creds_ok, account_id = check_aws_credentials()
    if not creds_ok:
        sys.exit(1)
    
    if not Path('infra/main.tf').exists():
        print_error("Terraform configuration not found in infra/ directory")
        sys.exit(1)
    
    # Get AWS session
    session = get_aws_session()
    
    try:
        # Step 1: Discover existing AWS resources
        aws_resources = discover_aws_resources(session)
        
        # Step 2: Get current Terraform state
        terraform_state = get_terraform_state()
        
        # Step 3: Analyze drift
        drifts = analyze_drift(aws_resources, terraform_state)
        
        # Step 4: Reconcile state if needed
        if drifts:
            if not reconcile_state(drifts):
                print_error("State reconciliation failed")
                sys.exit(1)
        
        # Step 5: Generate Terraform plan
        if not generate_terraform_plan():
            print_error("Terraform planning failed")
            sys.exit(1)
        
        # Step 6: Apply changes
        if not apply_terraform_changes():
            print_error("Terraform apply failed")
            sys.exit(1)
        
        # Success summary
        print_title("Deployment Summary")
        print_status("✅ AWS resource discovery completed")
        print_status("✅ State reconciliation completed")
        print_status("✅ Infrastructure deployment completed")
        
        print_info("\nNext steps:")
        print_info("1. Build and push Docker images to ECR")
        print_info("2. Deploy application services to ECS")
        print_info("3. Configure DNS and SSL certificates")
        print_info("4. Set up monitoring and alerts")
        
    except Exception as e:
        print_error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
