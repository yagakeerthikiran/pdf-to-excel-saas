#!/usr/bin/env python3
"""
🔧 INFRASTRUCTURE FIX AND COST OPTIMIZATION SCRIPT
=================================================

This script fixes the target group lifecycle issue and optimizes costs
by reducing NAT gateways from 2 to 1 and improving infrastructure efficiency.
"""

import subprocess
import json
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔧 FIXING TARGET GROUP LIFECYCLE AND OPTIMIZING COSTS")
    print("=" * 55)
    
    # Pull latest changes
    print("📥 Pulling latest Terraform fixes...")
    success, stdout, stderr = run_command("git pull origin feat/infrastructure-clean")
    if not success:
        print(f"❌ Git pull failed: {stderr}")
        return False
    
    print("✅ Latest fixes pulled")
    
    # Navigate to infra directory
    infra_dir = Path("infra")
    if not infra_dir.exists():
        print("❌ Infrastructure directory not found")
        return False
    
    # Run terraform plan to see changes
    print("\n🔍 Running Terraform plan...")
    success, stdout, stderr = run_command("terraform plan", cwd="infra")
    
    if success:
        print("✅ Terraform plan completed")
        # Show summary of changes
        if "Plan:" in stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'Plan:' in line:
                    print(f"📋 {line.strip()}")
                elif '# aws_lb_target_group' in line:
                    print(f"🎯 {line.strip()}")
    else:
        print(f"⚠️ Terraform plan issues: {stderr}")
    
    # Apply changes
    print("\n🚀 Ready to apply fixes...")
    print("This will:")
    print("  ✅ Fix target group lifecycle (create_before_destroy)")
    print("  ✅ Use name_prefix for replaceable target groups")
    print("  ✅ Create missing ECS services")
    
    confirm = input("\nApply infrastructure fixes? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Apply cancelled")
        return False
    
    print("\n🔧 Applying Terraform changes...")
    success, stdout, stderr = run_command("terraform apply -auto-approve", cwd="infra")
    
    if success:
        print("✅ Infrastructure fixes applied successfully!")
        print("\n📊 Checking ECS services...")
        
        # Check if services are running
        success, stdout, stderr = run_command("aws ecs list-services --cluster pdf-excel-saas-prod --region ap-southeast-2")
        if success:
            services = json.loads(stdout)
            print(f"🎯 Found {len(services.get('serviceArns', []))} ECS services")
            for service_arn in services.get('serviceArns', []):
                service_name = service_arn.split('/')[-1]
                print(f"   📦 {service_name}")
        
        print("\n🎉 INFRASTRUCTURE FIXES COMPLETED!")
        print("Next steps:")
        print("  1. ✅ Target groups can now be replaced without errors")
        print("  2. ✅ ECS services should be created and running")
        print("  3. 🧪 Test your ALB DNS for 200 responses (not 503)")
        print("  4. 📊 Monitor CloudWatch logs if tasks fail health checks")
        
        return True
    else:
        print(f"❌ Terraform apply failed: {stderr}")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
