#!/usr/bin/env python3
"""
Load Balancer Configuration Script - Production Ready
Configures ALB routing rules for PDF to Excel SaaS application.
Ensures proper routing between frontend and backend services.
"""
import boto3
import json
import sys
import time
from botocore.exceptions import ClientError

def get_load_balancer_info():
    """Get load balancer details from AWS"""
    region = 'ap-southeast-2'
    elbv2_client = boto3.client('elbv2', region_name=region)
    
    try:
        # Get load balancer by name pattern
        response = elbv2_client.describe_load_balancers()
        alb_arn = None
        alb_dns = None
        
        for lb in response['LoadBalancers']:
            if 'pdf-excel-saas-prod-alb' in lb['LoadBalancerName']:
                alb_arn = lb['LoadBalancerArn']
                alb_dns = lb['DNSName']
                print(f"✅ Found ALB: {lb['LoadBalancerName']}")
                print(f"   DNS: http://{alb_dns}")
                break
                
        if not alb_arn:
            print("❌ Could not find PDF Excel SaaS load balancer")
            return None, None
            
        return alb_arn, alb_dns
    except Exception as e:
        print(f"❌ Error getting load balancer info: {e}")
        return None, None

def get_target_groups():
    """Get target group ARNs"""
    region = 'ap-southeast-2'
    elbv2_client = boto3.client('elbv2', region_name=region)
    
    try:
        response = elbv2_client.describe_target_groups()
        frontend_tg = None
        backend_tg = None
        
        for tg in response['TargetGroups']:
            if 'frontend' in tg['TargetGroupName']:
                frontend_tg = tg['TargetGroupArn']
                print(f"✅ Found Frontend TG: {tg['TargetGroupName']}")
            elif 'backend' in tg['TargetGroupName']:
                backend_tg = tg['TargetGroupArn']
                print(f"✅ Found Backend TG: {tg['TargetGroupName']}")
                
        return frontend_tg, backend_tg
    except Exception as e:
        print(f"❌ Error getting target groups: {e}")
        return None, None

def configure_listener_rules(alb_arn, frontend_tg, backend_tg):
    """Configure ALB listener rules for proper routing"""
    region = 'ap-southeast-2'
    elbv2_client = boto3.client('elbv2', region_name=region)
    
    try:
        # Get listener
        listeners = elbv2_client.describe_listeners(LoadBalancerArn=alb_arn)
        if not listeners['Listeners']:
            print("❌ No listeners found on load balancer")
            return False
            
        listener_arn = listeners['Listeners'][0]['ListenerArn']
        print(f"✅ Found listener: {listener_arn}")
        
        # Get existing rules
        existing_rules = elbv2_client.describe_rules(ListenerArn=listener_arn)
        
        # Check if API rule exists
        api_rule_exists = False
        for rule in existing_rules['Rules']:
            if rule.get('Conditions'):
                for condition in rule.get('Conditions', []):
                    if condition.get('Field') == 'path-pattern':
                        values = condition.get('Values', [])
                        if '/api/*' in values:
                            api_rule_exists = True
                            print("✅ API routing rule already exists")
                            break
        
        # Create API rule if it doesn't exist
        if not api_rule_exists and backend_tg:
            print("🔧 Creating API routing rule...")
            try:
                response = elbv2_client.create_rule(
                    ListenerArn=listener_arn,
                    Priority=100,
                    Conditions=[
                        {
                            'Field': 'path-pattern',
                            'Values': ['/api/*']
                        }
                    ],
                    Actions=[
                        {
                            'Type': 'forward',
                            'TargetGroupArn': backend_tg
                        }
                    ]
                )
                print(f"✅ Created API routing rule successfully")
            except ClientError as e:
                if 'PriorityInUse' in str(e):
                    print("⚠️ Priority 100 already in use, trying 101...")
                    response = elbv2_client.create_rule(
                        ListenerArn=listener_arn,
                        Priority=101,
                        Conditions=[
                            {
                                'Field': 'path-pattern',
                                'Values': ['/api/*']
                            }
                        ],
                        Actions=[
                            {
                                'Type': 'forward',
                                'TargetGroupArn': backend_tg
                            }
                        ]
                    )
                    print(f"✅ Created API routing rule with priority 101")
                else:
                    raise e
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring listener rules: {e}")
        return False

def update_target_group_health_checks(frontend_tg, backend_tg):
    """Update target group health check configurations"""
    region = 'ap-southeast-2'
    elbv2_client = boto3.client('elbv2', region_name=region)
    
    try:
        # Update frontend health check to root path
        if frontend_tg:
            print("🔧 Updating frontend health check...")
            elbv2_client.modify_target_group(
                TargetGroupArn=frontend_tg,
                HealthCheckPath='/',
                HealthCheckIntervalSeconds=30,
                HealthCheckTimeoutSeconds=5,
                HealthyThresholdCount=2,
                UnhealthyThresholdCount=2
            )
            print("✅ Updated frontend target group health check")
        
        # Update backend health check to /api/health
        if backend_tg:
            print("🔧 Updating backend health check...")
            elbv2_client.modify_target_group(
                TargetGroupArn=backend_tg,
                HealthCheckPath='/api/health',
                HealthCheckIntervalSeconds=30,
                HealthCheckTimeoutSeconds=5,
                HealthyThresholdCount=2,
                UnhealthyThresholdCount=2
            )
            print("✅ Updated backend target group health check")
            
    except Exception as e:
        print(f"⚠️ Error updating health checks: {e}")

def check_target_health(frontend_tg, backend_tg):
    """Check the health of targets in both target groups"""
    region = 'ap-southeast-2'
    elbv2_client = boto3.client('elbv2', region_name=region)
    
    print("\n🏥 Checking Target Health...")
    
    try:
        if frontend_tg:
            health = elbv2_client.describe_target_health(TargetGroupArn=frontend_tg)
            print(f"\n📊 Frontend Target Group Health:")
            for target in health['TargetHealthDescriptions']:
                status = target['TargetHealth']['State']
                target_id = target['Target']['Id']
                reason = target['TargetHealth'].get('Description', '')
                print(f"   Target {target_id}: {status} {reason}")
                
        if backend_tg:
            health = elbv2_client.describe_target_health(TargetGroupArn=backend_tg)
            print(f"\n📊 Backend Target Group Health:")
            for target in health['TargetHealthDescriptions']:
                status = target['TargetHealth']['State']
                target_id = target['Target']['Id']
                reason = target['TargetHealth'].get('Description', '')
                print(f"   Target {target_id}: {status} {reason}")
                
    except Exception as e:
        print(f"❌ Error checking target health: {e}")

def main():
    """Main execution function"""
    print("🚀 PDF to Excel SaaS - Load Balancer Configuration")
    print("=" * 55)
    print("📍 Region: Sydney (ap-southeast-2)")
    print("")
    
    # Step 1: Get load balancer info
    print("🔍 Step 1: Finding Load Balancer...")
    alb_arn, alb_dns = get_load_balancer_info()
    if not alb_arn:
        print("❌ Could not find load balancer. Exiting.")
        sys.exit(1)
    
    # Step 2: Get target groups
    print("\n🎯 Step 2: Finding Target Groups...")
    frontend_tg, backend_tg = get_target_groups()
    if not frontend_tg or not backend_tg:
        print("⚠️ Could not find all target groups")
    
    # Step 3: Configure routing rules
    print("\n🔧 Step 3: Configuring Routing Rules...")
    if configure_listener_rules(alb_arn, frontend_tg, backend_tg):
        print("✅ Routing rules configured successfully")
    else:
        print("❌ Failed to configure routing rules")
    
    # Step 4: Update health checks
    print("\n🏥 Step 4: Updating Health Check Configuration...")
    update_target_group_health_checks(frontend_tg, backend_tg)
    
    # Step 5: Check target health
    check_target_health(frontend_tg, backend_tg)
    
    # Summary
    print("\n" + "=" * 55)
    print("📋 CONFIGURATION SUMMARY")
    print("=" * 55)
    print(f"🌐 Frontend URL: http://{alb_dns}")
    print(f"🔧 Backend API: http://{alb_dns}/api/health")
    print(f"📊 Routing: / → Frontend, /api/* → Backend")
    print(f"🏥 Health Checks: / (Frontend), /api/health (Backend)")
    
    print("\n💡 Next Steps:")
    print("1. Wait 2-3 minutes for health checks to pass")
    print("2. Test the endpoints above")
    print("3. Deploy updated containers if needed")
    print("4. Monitor target health until both are 'healthy'")
    
    print(f"\n🎉 Load balancer configuration complete!")
    print(f"🌏 Your SaaS is ready for Australian users!")

if __name__ == "__main__":
    main()
