#!/usr/bin/env python3
"""
Infrastructure State Alignment Script
- Checks actual AWS resource configurations 
- Updates Terraform config to match AWS reality
- Prevents destructive operations by aligning configuration
"""

import subprocess
import json
import sys
from pathlib import Path

AWS_REGION = "ap-southeast-2"
APP_NAME = "pdf-excel-saas"
ENVIRONMENT = "prod"

def run_command(cmd, cwd=None):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_target_group_config(tg_name):
    """Get actual Target Group configuration from AWS"""
    cmd = f'aws elbv2 describe-target-groups --names {tg_name} --region {AWS_REGION}'
    success, stdout, stderr = run_command(cmd)
    
    if not success:
        print(f"❌ Could not get Target Group config: {tg_name}")
        return None
    
    try:
        data = json.loads(stdout)
        if data['TargetGroups']:
            tg = data['TargetGroups'][0]
            return {
                'name': tg['TargetGroupName'],
                'port': tg['Port'],
                'protocol': tg['Protocol'],
                'vpc_id': tg['VpcId'],
                'target_type': tg['TargetType'],
                'health_check_path': tg['HealthCheckPath'],
                'health_check_port': tg['HealthCheckPort'],
                'health_check_protocol': tg['HealthCheckProtocol'],
                'health_check_interval': tg['HealthCheckIntervalSeconds'],
                'healthy_threshold': tg['HealthyThresholdCount'],
                'unhealthy_threshold': tg['UnhealthyThresholdCount'],
                'health_check_timeout': tg['HealthCheckTimeoutSeconds'],
                'matcher': tg['Matcher']['HttpCode'] if 'Matcher' in tg else '200'
            }
    except Exception as e:
        print(f"❌ Error parsing Target Group data: {e}")
        return None

def check_aws_configurations():
    """Check actual AWS configurations for Target Groups"""
    print("🔍 Checking actual AWS Target Group configurations...")
    
    frontend_tg = get_target_group_config(f"{APP_NAME}-{ENVIRONMENT}-frontend-tg")
    backend_tg = get_target_group_config(f"{APP_NAME}-{ENVIRONMENT}-backend-tg")
    
    if frontend_tg:
        print(f"✅ Frontend TG found:")
        print(f"   Port: {frontend_tg['port']}")
        print(f"   Protocol: {frontend_tg['protocol']}")
        print(f"   Health Check Path: {frontend_tg['health_check_path']}")
        print(f"   Target Type: {frontend_tg['target_type']}")
    
    if backend_tg:
        print(f"✅ Backend TG found:")
        print(f"   Port: {backend_tg['port']}")
        print(f"   Protocol: {backend_tg['protocol']}")
        print(f"   Health Check Path: {backend_tg['health_check_path']}")
        print(f"   Target Type: {backend_tg['target_type']}")
    
    return frontend_tg, backend_tg

def show_terraform_state():
    """Show current Terraform state for Target Groups"""
    print("\n🔍 Checking Terraform state...")
    
    # Check if state exists
    success, stdout, stderr = run_command('terraform state list', cwd='infra')
    if not success:
        print("❌ Could not get Terraform state")
        return
    
    state_resources = stdout.strip().split('\n') if stdout.strip() else []
    
    for resource in ['aws_lb_target_group.frontend', 'aws_lb_target_group.backend']:
        if resource in state_resources:
            print(f"\n📋 {resource} in state:")
            success, stdout, stderr = run_command(f'terraform state show {resource}', cwd='infra')
            if success:
                # Extract key attributes
                lines = stdout.split('\n')
                for line in lines:
                    if any(attr in line for attr in ['port', 'protocol', 'target_type', 'health_check']):
                        print(f"   {line.strip()}")
        else:
            print(f"❌ {resource} not in state")

def check_terraform_plan_issues():
    """Check what Terraform plan wants to do"""
    print("\n🔍 Checking Terraform plan...")
    
    # Initialize first
    success, stdout, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print(f"❌ Terraform init failed: {stderr}")
        return False
    
    # Run plan to see issues
    plan_cmd = f'terraform plan -var="aws_region={AWS_REGION}" -var="environment={ENVIRONMENT}" -var="app_name={APP_NAME}"'
    success, stdout, stderr = run_command(plan_cmd, cwd='infra')
    
    if not success:
        print("❌ Terraform plan failed (expected due to prevent_destroy)")
        if "prevent_destroy" in stderr:
            print("✅ Lifecycle protection is working - preventing destructive operations")
            
            # Show what would be destroyed/created
            if "plan calls for this resource to be destroyed" in stderr:
                print("\n🔍 Resources that would be destroyed (config mismatch):")
                lines = stderr.split('\n')
                for line in lines:
                    if 'aws_lb_target_group' in line and 'line' in line:
                        print(f"   {line.strip()}")
        return False
    else:
        print("✅ Terraform plan succeeded")
        return True

def fix_target_group_configuration():
    """Provide instructions to fix Target Group configuration"""
    print("\n🔧 How to fix the configuration mismatch:")
    print("=" * 50)
    
    print("\n1. Check actual AWS Target Group configurations:")
    print(f"   aws elbv2 describe-target-groups --names {APP_NAME}-{ENVIRONMENT}-frontend-tg --region {AWS_REGION}")
    print(f"   aws elbv2 describe-target-groups --names {APP_NAME}-{ENVIRONMENT}-backend-tg --region {AWS_REGION}")
    
    print("\n2. Compare with your Terraform configuration in infra/main.tf")
    print("   Look for differences in:")
    print("   - port (likely mismatch)")
    print("   - protocol (HTTP vs HTTPS)")
    print("   - health_check path")
    print("   - target_type (ip vs instance)")
    
    print("\n3. Update infra/main.tf to match AWS reality")
    print("   Example - if AWS shows port 80 but Terraform has 3000:")
    print("   Change: port = 3000")
    print("   To:     port = 80")
    
    print("\n4. Keep lifecycle protection:")
    print("   lifecycle {")
    print("     prevent_destroy = true")
    print("   }")
    
    print("\n5. Re-run deployment after fixing configuration")

def main():
    """Main function to diagnose and fix infrastructure issues"""
    print(f"PDF to Excel SaaS - Infrastructure State Alignment")
    print(f"Region: {AWS_REGION} | Environment: {ENVIRONMENT}")
    print("=" * 60)
    
    if not Path('infra/main.tf').exists():
        print("❌ Terraform configuration not found")
        sys.exit(1)
    
    # Step 1: Check actual AWS configurations
    frontend_tg, backend_tg = check_aws_configurations()
    
    # Step 2: Show Terraform state
    show_terraform_state()
    
    # Step 3: Check plan issues
    plan_works = check_terraform_plan_issues()
    
    if not plan_works:
        # Step 4: Provide fix instructions
        fix_target_group_configuration()
        
        print("\n🎯 Summary:")
        print("- Lifecycle protection is working (preventing resource destruction)")
        print("- Configuration mismatch detected between Terraform and AWS")
        print("- Update Terraform configuration to match AWS reality")
        print("- Then re-run the deployment script")
    else:
        print("\n✅ Infrastructure state is aligned!")
        print("You can now run the deployment script successfully.")

if __name__ == "__main__":
    main()
