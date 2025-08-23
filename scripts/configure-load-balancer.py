#!/usr/bin/env python3
"""
Load Balancer Configuration Script
Adds missing API routing rules to the ALB for proper backend traffic routing.
"""
import boto3
import json
import sys

def configure_load_balancer_rules():
    """Configure ALB listener rules for proper API routing"""
    
    # AWS configuration
    region = 'ap-southeast-2'
    
    # Initialize clients
    elbv2_client = boto3.client('elbv2', region_name=region)
    
    try:
        # Get listener details
        listeners = elbv2_client.describe_listeners(
            LoadBalancerArn='arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:loadbalancer/app/pdf-excel-saas-prod-alb/7a586ade06ef40ef'
        )
        
        listener_arn = listeners['Listeners'][0]['ListenerArn']
        print(f"Found listener: {listener_arn}")
        
        # Check existing rules
        existing_rules = elbv2_client.describe_rules(ListenerArn=listener_arn)
        api_rule_exists = any(
            rule.get('Conditions') and 
            any(condition.get('Field') == 'path-pattern' and 
                '/api/*' in condition.get('Values', []) 
                for condition in rule.get('Conditions', []))
            for rule in existing_rules['Rules']
        )
        
        if api_rule_exists:
            print("API routing rule already exists")
            return True
            
        # Create API routing rule
        print("Creating API routing rule...")
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
                    'TargetGroupArn': 'arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:targetgroup/pdf-excel-saas-prod-backend-tg1/624d10cc4f445c11'
                }
            ]
        )
        
        print(f"✅ Created API routing rule: {response['Rules'][0]['RuleArn']}")
        
        # Update backend target group health check path
        print("Updating backend target group health check...")
        elbv2_client.modify_target_group(
            TargetGroupArn='arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:targetgroup/pdf-excel-saas-prod-backend-tg1/624d10cc4f445c11',
            HealthCheckPath='/api/health'
        )
        
        print("✅ Updated backend target group health check path to /api/health")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring load balancer: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("🔧 Configuring Load Balancer Rules...")
    print("=" * 50)
    
    success = configure_load_balancer_rules()
    
    if success:
        print("\n✅ Load balancer configuration completed successfully!")
        print("\nNext steps:")
        print("1. Pull the latest code changes")
        print("2. Rebuild and deploy containers") 
        print("3. Test the endpoints")
    else:
        print("\n❌ Load balancer configuration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
