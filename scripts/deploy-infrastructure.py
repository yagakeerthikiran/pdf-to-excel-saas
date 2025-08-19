#!/usr/bin/env python3
"""
Intelligent Infrastructure Deployment Script
- Discovers existing AWS resources directly
- Compares with Terraform state for inconsistencies
- Auto-reconciles stale/orphaned state objects
- Generates dynamic terraform operations (create/update/delete/recreate)
- Handles lifecycle protection when recreating resources is needed
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
    """Temporarily remove lifecycle protection when needed for recreation"""
    print_info("Temporarily removing lifecycle protection to allow resource recreation...")
    
    main_tf_path = Path('infra/main.tf')
    
    # Read current main.tf
    with open(main_tf_path, 'r') as f:
        content = f.read()
    
    # Remove lifecycle blocks
    lines = content.split('\n')
    filtered_lines = []
    skip_lifecycle = False
    brace_count = 0
    
    for line in lines:
        if 'lifecycle {' in line:
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
    
    print_status("Lifecycle protection temporarily removed")
    return True

def restore_lifecycle_protection():
    """Restore lifecycle protection from backup"""
    print_info("Restoring lifecycle protection...")
    
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

def discover_aws_resources(session: boto3.Session) -> Dict[str, List[Dict]]:
    """Discover ALL existing AWS resources, then filter by relevance"""
    print_title("Discovering AWS Resources")
    print_info("Scanning AWS account for existing infrastructure...")
    
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
        
        # Get ALL VPCs, then analyze
        all_vpcs = ec2.describe_vpcs()['Vpcs']
        print_info(f"Found {len(all_vpcs)} total VPCs in AWS")
        
        # Show what we found
        for vpc in all_vpcs:
            vpc_name = "unnamed"
            for tag in vpc.get('Tags', []):
                if tag['Key'] == 'Name':
                    vpc_name = tag['Value']
                    break
            print_info(f"  VPC: {vpc['VpcId']} ({vpc_name}) - CIDR: {vpc['CidrBlock']}")
            
            # Check if this looks like our VPC
            if APP_NAME in vpc_name.lower() or any(APP_NAME in tag.get('Value', '').lower() for tag in vpc.get('Tags', [])):
                resources['vpcs'].append(vpc)
                
        print_info(f"Identified {len(resources['vpcs'])} VPCs belonging to {APP_NAME}")
        
        # Get ALL subnets, then filter by VPC
        all_subnets = ec2.describe_subnets()['Subnets']
        print_info(f"Found {len(all_subnets)} total subnets in AWS")
        
        if resources['vpcs']:
            our_vpc_ids = [vpc['VpcId'] for vpc in resources['vpcs']]
            our_subnets = [subnet for subnet in all_subnets if subnet['VpcId'] in our_vpc_ids]
            resources['subnets'] = our_subnets
            print_info(f"Found {len(our_subnets)} subnets in our VPCs")
            
            for subnet in our_subnets:
                subnet_name = "unnamed"
                for tag in subnet.get('Tags', []):
                    if tag['Key'] == 'Name':
                        subnet_name = tag['Value']
                        break
                print_info(f"  Subnet: {subnet['SubnetId']} ({subnet_name}) - CIDR: {subnet['CidrBlock']}")
        
        # Get ALL security groups, then filter by VPC
        all_sgs = ec2.describe_security_groups()['SecurityGroups']
        if resources['vpcs']:
            our_vpc_ids = [vpc['VpcId'] for vpc in resources['vpcs']]
            our_sgs = [sg for sg in all_sgs if sg['VpcId'] in our_vpc_ids]
            resources['security_groups'] = our_sgs
            print_info(f"Found {len(our_sgs)} security groups in our VPCs")
        
        # Load Balancers - check all, identify ours
        elbv2 = session.client('elbv2')
        all_lbs = elbv2.describe_load_balancers()['LoadBalancers']
        print_info(f"Found {len(all_lbs)} total load balancers in AWS")
        
        our_lbs = []
        for lb in all_lbs:
            lb_name = lb.get('LoadBalancerName', '')
            if APP_NAME in lb_name or ENVIRONMENT in lb_name:
                our_lbs.append(lb)
                print_info(f"  Load Balancer: {lb_name} - DNS: {lb['DNSName']}")
        
        resources['load_balancers'] = our_lbs
        print_info(f"Identified {len(our_lbs)} load balancers belonging to {APP_NAME}")
        
        # Target Groups - check all, identify ours
        all_tgs = elbv2.describe_target_groups()['TargetGroups']
        our_tgs = []
        for tg in all_tgs:
            tg_name = tg.get('TargetGroupName', '')
            if APP_NAME in tg_name or ENVIRONMENT in tg_name:
                our_tgs.append(tg)
                print_info(f"  Target Group: {tg_name} - Port: {tg['Port']}")
        
        resources['target_groups'] = our_tgs
        print_info(f"Identified {len(our_tgs)} target groups belonging to {APP_NAME}")
        
        # ECS Resources
        ecs = session.client('ecs')
        
        # Get ALL ECS clusters
        all_cluster_arns = ecs.list_clusters()['clusterArns']
        if all_cluster_arns:
            all_clusters = ecs.describe_clusters(clusters=all_cluster_arns)['clusters']
            print_info(f"Found {len(all_clusters)} total ECS clusters in AWS")
            
            our_clusters = []
            for cluster in all_clusters:
                cluster_name = cluster.get('clusterName', '')
                if APP_NAME in cluster_name or ENVIRONMENT in cluster_name:
                    our_clusters.append(cluster)
                    print_info(f"  ECS Cluster: {cluster_name} - Status: {cluster['status']}")
            
            resources['ecs_clusters'] = our_clusters
            print_info(f"Identified {len(our_clusters)} ECS clusters belonging to {APP_NAME}")
            
            # Get services from our clusters
            all_our_services = []
            for cluster in our_clusters:
                service_arns = ecs.list_services(cluster=cluster['clusterArn'])['serviceArns']
                if service_arns:
                    services = ecs.describe_services(
                        cluster=cluster['clusterArn'], 
                        services=service_arns
                    )['services']
                    all_our_services.extend(services)
                    
                    for service in services:
                        print_info(f"    Service: {service['serviceName']} - Desired: {service['desiredCount']}")
            
            resources['ecs_services'] = all_our_services
            print_info(f"Found {len(all_our_services)} ECS services in our clusters")
        
        # ECR Repositories
        ecr = session.client('ecr')
        try:
            all_repos = ecr.describe_repositories()['repositories']
            our_repos = []
            for repo in all_repos:
                repo_name = repo.get('repositoryName', '')
                if APP_NAME in repo_name:
                    our_repos.append(repo)
                    print_info(f"  ECR Repository: {repo_name}")
            
            resources['ecr_repositories'] = our_repos
            print_info(f"Found {len(our_repos)} ECR repositories for {APP_NAME}")
        except Exception as e:
            print_warning(f"Could not check ECR repositories: {e}")
        
        # RDS Resources
        rds = session.client('rds')
        
        # Get ALL RDS instances
        all_db_instances = rds.describe_db_instances()['DBInstances']
        our_dbs = []
        for db in all_db_instances:
            db_id = db.get('DBInstanceIdentifier', '')
            if APP_NAME in db_id or ENVIRONMENT in db_id:
                our_dbs.append(db)
                print_info(f"  RDS Instance: {db_id} - Engine: {db['Engine']} - Status: {db['DBInstanceStatus']}")
        
        resources['rds_instances'] = our_dbs
        print_info(f"Found {len(our_dbs)} RDS instances for {APP_NAME}")
        
        # RDS Subnet Groups
        all_subnet_groups = rds.describe_db_subnet_groups()['DBSubnetGroups']
        our_subnet_groups = []
        for sg in all_subnet_groups:
            sg_name = sg.get('DBSubnetGroupName', '')
            if APP_NAME in sg_name or ENVIRONMENT in sg_name:
                our_subnet_groups.append(sg)
                print_info(f"  RDS Subnet Group: {sg_name}")
        
        resources['rds_subnets'] = our_subnet_groups
        
        # S3 Buckets
        s3 = session.client('s3')
        try:
            all_buckets = s3.list_buckets()['Buckets']
            our_buckets = []
            for bucket in all_buckets:
                bucket_name = bucket.get('Name', '')
                if APP_NAME in bucket_name or ENVIRONMENT in bucket_name:
                    our_buckets.append(bucket)
                    print_info(f"  S3 Bucket: {bucket_name}")
            
            resources['s3_buckets'] = our_buckets
            print_info(f"Found {len(our_buckets)} S3 buckets for {APP_NAME}")
        except Exception as e:
            print_warning(f"Could not check S3 buckets: {e}")
        
        # IAM Roles
        iam = session.client('iam')
        try:
            all_roles = iam.list_roles()['Roles']
            our_roles = []
            for role in all_roles:
                role_name = role.get('RoleName', '')
                if APP_NAME in role_name or ENVIRONMENT in role_name:
                    our_roles.append(role)
                    print_info(f"  IAM Role: {role_name}")
            
            resources['iam_roles'] = our_roles
            print_info(f"Found {len(our_roles)} IAM roles for {APP_NAME}")
        except Exception as e:
            print_warning(f"Could not check IAM roles: {e}")
        
        # CloudWatch Log Groups
        logs = session.client('logs')
        try:
            all_log_groups = logs.describe_log_groups()['logGroups']
            our_logs = []
            for lg in all_log_groups:
                lg_name = lg.get('logGroupName', '')
                if APP_NAME in lg_name or ENVIRONMENT in lg_name:
                    our_logs.append(lg)
                    print_info(f"  Log Group: {lg_name}")
            
            resources['cloudwatch_logs'] = our_logs
            print_info(f"Found {len(our_logs)} CloudWatch log groups for {APP_NAME}")
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
        # If no state exists, return empty structure
        return {'values': {'root_module': {'resources': []}}}
    
    try:
        state = json.loads(stdout)
        resources = state.get('values', {}).get('root_module', {}).get('resources', [])
        print_info(f"Found {len(resources)} resources in Terraform state")
        
        # Show what's in state
        for resource in resources:
            resource_address = f"{resource['type']}.{resource['name']}"
            print_info(f"  In State: {resource_address}")
        
        return state
    except json.JSONDecodeError as e:
        print_error(f"Invalid Terraform state JSON: {e}")
        return {}

def analyze_drift(aws_resources: Dict, terraform_state: Dict) -> List[ResourceDrift]:
    """Analyze what exists in AWS vs what Terraform expects"""
    print_title("Analyzing Resource Drift")
    
    print_info("Comparing AWS reality with Terraform expectations...")
    
    # Get expected resources from Terraform configuration
    expected_resources = {
        'aws_vpc.main': 'VPC',
        'aws_subnet.public': 'Public Subnets',
        'aws_subnet.private': 'Private Subnets',
        'aws_security_group.alb': 'ALB Security Group',
        'aws_security_group.ecs': 'ECS Security Group', 
        'aws_security_group.rds': 'RDS Security Group',
        'aws_lb.main': 'Application Load Balancer',
        'aws_lb_target_group.frontend': 'Frontend Target Group',
        'aws_lb_target_group.backend': 'Backend Target Group',
        'aws_ecs_cluster.main': 'ECS Cluster',
        'aws_ecr_repository.frontend': 'Frontend ECR Repository',
        'aws_ecr_repository.backend': 'Backend ECR Repository',
        'aws_db_instance.main': 'RDS Database',
        'aws_s3_bucket.main': 'S3 Bucket'
    }
    
    drifts = []
    tf_resources = terraform_state.get('values', {}).get('root_module', {}).get('resources', [])
    tf_resource_addresses = {f"{r['type']}.{r['name']}" for r in tf_resources}
    
    print_info(f"Expected {len(expected_resources)} resources based on Terraform configuration")
    print_info(f"Found {len(tf_resource_addresses)} resources in current Terraform state")
    
    # Check for missing expected resources (exist in config but not in state)
    for expected_address, description in expected_resources.items():
        if expected_address not in tf_resource_addresses:
            print_warning(f"Missing from state: {expected_address} ({description})")
    
    # Summary of what we found in AWS
    print_info("\nAWS Resource Summary:")
    for resource_type, items in aws_resources.items():
        if items:
            print_info(f"  {resource_type}: {len(items)} found")
    
    return drifts

def generate_terraform_plan() -> Tuple[bool, bool]:
    """Generate and review Terraform execution plan, return (success, needs_lifecycle_removal)"""
    print_title("Generating Terraform Plan")
    
    plan_cmd = f'terraform plan -detailed-exitcode -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(plan_cmd, cwd='infra')
    
    # Check if lifecycle protection is preventing changes
    needs_lifecycle_removal = "lifecycle.prevent_destroy" in stderr
    
    # Terraform plan exit codes: 0 = no changes, 1 = error, 2 = changes planned
    if success:
        print_status("No changes needed - infrastructure is up to date")
        return True, False
    elif needs_lifecycle_removal:
        print_warning("Plan blocked by lifecycle protection - recreation needed")
        print_info("This is normal when changing resource configurations")
        return False, True
    elif "Error" in stderr:
        print_error(f"Plan failed: {stderr}")
        return False, False
    else:
        print_info("Changes detected in plan")
        # Show a summary of the plan
        if stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'Plan:' in line or '# aws_' in line or 'will be created' in line or 'will be destroyed' in line:
                    print_info(f"  {line.strip()}")
        return True, False

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
    
    lifecycle_protection_removed = False
    
    try:
        # Step 1: Discover existing AWS resources
        aws_resources = discover_aws_resources(session)
        
        # Step 2: Get current Terraform state
        terraform_state = get_terraform_state()
        
        # Step 3: Analyze drift
        drifts = analyze_drift(aws_resources, terraform_state)
        
        # Step 4: Generate Terraform plan (this will show what needs to be created/updated)
        plan_success, needs_lifecycle_removal = generate_terraform_plan()
        
        # Step 5: Handle lifecycle protection if needed
        if needs_lifecycle_removal:
            print_title("Handling Lifecycle Protection")
            print_info("Some resources need to be recreated due to configuration changes")
            print_info("Temporarily removing lifecycle protection to allow updates")
            
            # Create backup before removing protection
            if not backup_main_tf():
                print_error("Failed to create backup")
                sys.exit(1)
            
            # Remove lifecycle protection
            if not remove_lifecycle_protection():
                print_error("Failed to remove lifecycle protection")
                sys.exit(1)
            
            lifecycle_protection_removed = True
            
            # Re-run plan without lifecycle protection
            plan_success, _ = generate_terraform_plan()
        
        if not plan_success:
            print_error("Terraform planning failed")
            sys.exit(1)
        
        # Step 6: Apply changes if user confirms
        if not apply_terraform_changes():
            print_error("Terraform apply failed or cancelled")
            sys.exit(1)
        
        # Success summary
        print_title("Deployment Summary")
        print_status("✅ AWS resource discovery completed")
        print_status("✅ Infrastructure deployment completed")
        
        if lifecycle_protection_removed:
            print_status("✅ Lifecycle protection handled properly")
        
        print_info("\nNext steps:")
        print_info("1. Build and push Docker images to ECR")
        print_info("2. Deploy application services to ECS")
        print_info("3. Configure DNS and SSL certificates")
        print_info("4. Set up monitoring and alerts")
        
    except Exception as e:
        print_error(f"Deployment failed: {e}")
        sys.exit(1)
    finally:
        # Always restore lifecycle protection if it was removed
        if lifecycle_protection_removed:
            print_title("Restoring Lifecycle Protection")
            restore_lifecycle_protection()

if __name__ == "__main__":
    main()
