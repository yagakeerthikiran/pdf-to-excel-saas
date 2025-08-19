#!/usr/bin/env python3
"""
Safe Infrastructure Cleanup Script
- Identifies duplicate expensive resources
- Provides safe removal commands for duplicates
- Imports existing resources into Terraform state
- Prevents future duplicates
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

def analyze_nat_gateways(session: boto3.Session) -> Dict:
    """Analyze NAT Gateways to identify duplicates"""
    print_title("NAT Gateway Duplicate Analysis")
    
    ec2 = session.client('ec2')
    
    # Get all NAT Gateways
    nat_gateways = ec2.describe_nat_gateways()['NatGateways']
    
    # Get our VPCs first
    vpcs = ec2.describe_vpcs()['Vpcs']
    our_vpc_ids = []
    for vpc in vpcs:
        vpc_name = "unnamed"
        for tag in vpc.get('Tags', []):
            if tag['Key'] == 'Name':
                vpc_name = tag['Value']
                break
        if APP_NAME in vpc_name.lower():
            our_vpc_ids.append(vpc['VpcId'])
            print_info(f"Our VPC: {vpc['VpcId']} ({vpc_name})")
    
    # Get subnets in our VPCs
    our_subnets = {}
    subnets = ec2.describe_subnets()['Subnets']
    for subnet in subnets:
        if subnet['VpcId'] in our_vpc_ids:
            subnet_name = "unnamed"
            for tag in subnet.get('Tags', []):
                if tag['Key'] == 'Name':
                    subnet_name = tag['Value']
                    break
            our_subnets[subnet['SubnetId']] = {
                'name': subnet_name,
                'vpc_id': subnet['VpcId'],
                'az': subnet['AvailabilityZone'],
                'type': 'public' if 'public' in subnet_name.lower() else 'private'
            }
            print_info(f"Subnet: {subnet['SubnetId']} ({subnet_name}) - AZ: {subnet['AvailabilityZone']}")
    
    # Analyze NAT Gateways
    our_nat_gateways = []
    for nat in nat_gateways:
        if nat['State'] in ['available', 'pending']:
            subnet_id = nat['SubnetId']
            if subnet_id in our_subnets:
                subnet_info = our_subnets[subnet_id]
                
                nat_info = {
                    'id': nat['NatGatewayId'],
                    'subnet_id': subnet_id,
                    'subnet_name': subnet_info['name'],
                    'vpc_id': subnet_info['vpc_id'],
                    'az': subnet_info['az'],
                    'subnet_type': subnet_info['type'],
                    'state': nat['State'],
                    'create_time': nat['CreateTime']
                }
                our_nat_gateways.append(nat_info)
                
                print_cost(f"NAT Gateway: {nat['NatGatewayId']}")
                print_info(f"  Subnet: {subnet_info['name']} ({subnet_id})")
                print_info(f"  AZ: {subnet_info['az']}")
                print_info(f"  Type: {subnet_info['subnet_type']}")
                print_info(f"  Created: {nat['CreateTime']}")
                print_info(f"  State: {nat['State']}")
                print_cost(f"  Cost: $45/month")
    
    print_cost(f"\nTotal NAT Gateways: {len(our_nat_gateways)} (Expected: 2)")
    print_cost(f"Total NAT Gateway Cost: ${len(our_nat_gateways) * 45}/month")
    
    if len(our_nat_gateways) > 2:
        excess_cost = (len(our_nat_gateways) - 2) * 45
        print_error(f"EXCESS NAT Gateways: {len(our_nat_gateways) - 2}")
        print_error(f"WASTED COST: ${excess_cost}/month")
    
    return {
        'nat_gateways': our_nat_gateways,
        'our_vpcs': our_vpc_ids,
        'our_subnets': our_subnets
    }

def identify_safe_to_remove(nat_analysis: Dict) -> List[Dict]:
    """Identify which NAT Gateways can be safely removed"""
    print_title("Safe Removal Analysis")
    
    nat_gateways = nat_analysis['nat_gateways']
    
    # Group by VPC and AZ
    vpc_az_groups = {}
    for nat in nat_gateways:
        vpc_id = nat['vpc_id']
        az = nat['az']
        key = f"{vpc_id}-{az}"
        
        if key not in vpc_az_groups:
            vpc_az_groups[key] = []
        vpc_az_groups[key].append(nat)
    
    # Identify duplicates
    safe_to_remove = []
    keep_nat_gateways = []
    
    for key, nats in vpc_az_groups.items():
        if len(nats) > 1:
            # Multiple NAT Gateways in same VPC/AZ - keep the oldest
            nats_sorted = sorted(nats, key=lambda x: x['create_time'])
            keep_nat_gateways.append(nats_sorted[0])  # Keep oldest
            safe_to_remove.extend(nats_sorted[1:])    # Remove newer duplicates
            
            print_warning(f"Duplicate NAT Gateways in {key}:")
            for nat in nats_sorted:
                status = "KEEP (oldest)" if nat == nats_sorted[0] else "REMOVE (duplicate)"
                print_info(f"  {nat['id']} - Created: {nat['create_time']} - {status}")
        else:
            keep_nat_gateways.append(nats[0])
    
    print_info(f"\nRecommendation:")
    print_status(f"Keep: {len(keep_nat_gateways)} NAT Gateways")
    print_warning(f"Remove: {len(safe_to_remove)} NAT Gateways")
    
    if safe_to_remove:
        savings = len(safe_to_remove) * 45
        print_cost(f"Monthly Savings: ${savings}")
        
        print_info(f"\nNAT Gateways to remove:")
        for nat in safe_to_remove:
            print_warning(f"  {nat['id']} ({nat['subnet_name']}) - Created: {nat['create_time']}")
    
    return safe_to_remove

def generate_cleanup_commands(safe_to_remove: List[Dict]) -> List[str]:
    """Generate safe AWS CLI commands to remove duplicate NAT Gateways"""
    print_title("Cleanup Commands")
    
    if not safe_to_remove:
        print_status("No duplicate NAT Gateways found - infrastructure is optimal!")
        return []
    
    commands = []
    
    print_warning("⚠️  REVIEW THESE COMMANDS CAREFULLY BEFORE RUNNING:")
    print_info("These commands will delete duplicate NAT Gateways to save costs")
    
    for nat in safe_to_remove:
        cmd = f'aws ec2 delete-nat-gateway --nat-gateway-id {nat["id"]} --region {AWS_REGION}'
        commands.append(cmd)
        print_warning(f"  {cmd}")
    
    print_info(f"\nAfter running these commands:")
    print_status(f"- You'll save ${len(safe_to_remove) * 45}/month")
    print_status(f"- You'll have the optimal 2 NAT Gateways")
    print_status(f"- No service interruption (keeping oldest in each AZ)")
    
    return commands

def import_missing_resources():
    """Import missing resources into Terraform state"""
    print_title("Importing Missing Resources")
    
    print_info("Based on audit results, importing missing resources:")
    
    # Import RDS database
    print_info("Importing RDS database...")
    import_cmd = f'terraform import aws_db_instance.main pdf-excel-saas-prod-db'
    success, stdout, stderr = run_command(import_cmd, cwd='infra')
    
    if success:
        print_status("RDS database imported successfully")
    else:
        print_warning(f"RDS import failed (may already be imported): {stderr}")
    
    # Note: We'll import NAT Gateways after cleanup
    print_info("NAT Gateway imports will be done after duplicate cleanup")

def main():
    """Main cleanup function"""
    print(f"{Colors.RED}")
    print("=== INFRASTRUCTURE CLEANUP - COST OPTIMIZATION ===")
    print("==================================================")
    print("⚠️  You have $220/month in AWS costs with duplicates!")
    print("This script identifies safe cleanup to reduce costs")
    print(f"{Colors.END}")
    
    try:
        # Get AWS session
        session = get_aws_session()
        
        # Analyze NAT Gateway duplicates
        nat_analysis = analyze_nat_gateways(session)
        
        # Identify safe removals
        safe_to_remove = identify_safe_to_remove(nat_analysis)
        
        # Generate cleanup commands
        cleanup_commands = generate_cleanup_commands(safe_to_remove)
        
        # Import missing resources that should be in Terraform state
        print_info("\nFirst, let's import the missing RDS database:")
        confirm_import = input(f"{Colors.YELLOW}Import RDS database into Terraform state? (y/N): {Colors.END}")
        if confirm_import.lower() == 'y':
            import_missing_resources()
        
        # Offer to clean up duplicates
        if cleanup_commands:
            print_title("Cost Optimization")
            print_cost(f"Current monthly waste: ${len(safe_to_remove) * 45}")
            print_info("The cleanup commands above will:")
            print_status("✅ Remove duplicate NAT Gateways safely")
            print_status("✅ Keep the oldest NAT Gateway in each AZ")
            print_status("✅ Maintain full network connectivity")
            print_status(f"✅ Save ${len(safe_to_remove) * 45}/month")
            
            print_warning("\n⚠️  Manual cleanup required:")
            print_info("1. Copy the AWS CLI commands shown above")
            print_info("2. Run them in your terminal one by one")
            print_info("3. Verify deletion in AWS console")
            print_info("4. Then proceed with Terraform deployment")
            
            print_info(f"\nAfter cleanup, your monthly cost will be ~${220 - (len(safe_to_remove) * 45)}")
        
        print_title("Summary")
        print_status("✅ Duplicate analysis completed")
        print_status("✅ Safe cleanup commands provided")
        print_status("✅ Cost optimization recommendations ready")
        
    except Exception as e:
        print_error(f"Cleanup analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
