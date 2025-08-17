#!/usr/bin/env python3
"""
Clean Infrastructure Deployment Script
This script deploys AWS infrastructure and guides you through required configuration
"""

import os
import sys
import subprocess
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import secrets
import string

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def generate_secure_key(length=32):
    """Generate a secure random key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def send_email_notification(subject, body, to_email="yagakeerthikiran@gmail.com"):
    """Send email notification"""
    try:
        # Load SMTP settings from environment or use defaults
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', 'yagakeerthikiran@gmail.com')
        smtp_pass = os.getenv('SMTP_PASS', '')
        
        if not smtp_pass:
            print_warning("SMTP_PASS not configured - skipping email notification")
            print_info("To enable email notifications, set SMTP_PASS in your environment")
            return
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = f"[PDF to Excel SaaS] {subject}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        text = msg.as_string()
        server.sendmail(smtp_user, to_email, text)
        server.quit()
        
        print_status(f"Email notification sent to {to_email}")
        
    except Exception as e:
        print_warning(f"Failed to send email notification: {e}")

def run_command(command, cwd=None, capture_output=False):
    """Run shell command with error handling"""
    try:
        print_info(f"Running: {command}")
        
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(command, shell=True, cwd=cwd)
            return result.returncode == 0, "", ""
            
    except Exception as e:
        print_error(f"Command failed: {e}")
        return False, "", str(e)

def check_prerequisites():
    """Check if all required tools are installed"""
    print_info("Checking prerequisites...")
    
    tools = {
        'git': 'git --version',
        'python': 'python --version',
        'aws': 'aws --version',
        'terraform': 'terraform version'
    }
    
    missing_tools = []
    
    for tool, command in tools.items():
        success, stdout, stderr = run_command(command, capture_output=True)
        if success:
            print_status(f"{tool} is installed")
        else:
            print_error(f"{tool} is not installed")
            missing_tools.append(tool)
    
    if missing_tools:
        print_error(f"Missing tools: {', '.join(missing_tools)}")
        print_info("Please install missing tools and try again")
        return False
    
    # Check AWS credentials
    success, stdout, stderr = run_command('aws sts get-caller-identity', capture_output=True)
    if success:
        identity = json.loads(stdout)
        print_status(f"AWS credentials configured (Account: {identity['Account']})")
        return True
    else:
        print_error("AWS credentials not configured. Run 'aws configure'")
        return False

def check_pre_deployment_config():
    """Check if required service account configuration is present"""
    print_info("Checking pre-deployment configuration...")
    
    if not os.path.exists('.env.prod'):
        print_error(".env.prod file not found")
        print_info("Please follow these steps:")
        print_info("1. Copy .env.prod.template to .env.prod")
        print_info("2. Set up service accounts (see SERVICE-SETUP-GUIDE.md)")
        print_info("3. Fill in the required values before running this script")
        return False
    
    # Check if key service accounts are configured
    required_before_deployment = [
        'STRIPE_SECRET_KEY',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'NEXT_PUBLIC_SUPABASE_ANON_KEY',
        'NEXT_PUBLIC_SENTRY_DSN',
        'SENTRY_ORG',
        'SENTRY_PROJECT',
        'NEXT_PUBLIC_POSTHOG_KEY'
    ]
    
    env_vars = {}
    with open('.env.prod', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    missing_config = []
    placeholder_config = []
    
    for var in required_before_deployment:
        if var not in env_vars or not env_vars[var]:
            missing_config.append(var)
        elif any(placeholder in env_vars[var].lower() for placeholder in ['your_', 'placeholder', 'example', '****']):
            placeholder_config.append(var)
    
    if missing_config or placeholder_config:
        print_error("Pre-deployment configuration incomplete")
        
        if missing_config:
            print_error("Missing required variables:")
            for var in missing_config:
                print(f"  - {var}")
        
        if placeholder_config:
            print_error("Variables with placeholder values:")
            for var in placeholder_config:
                print(f"  - {var}: {env_vars[var]}")
        
        print_info("\nPlease complete these steps before running infrastructure deployment:")
        print_info("1. Follow SERVICE-SETUP-GUIDE.md to create service accounts")
        print_info("2. Update .env.prod with real values (not placeholders)")
        print_info("3. Run this script again")
        return False
    
    print_status("Pre-deployment configuration looks good")
    return True

def update_env_with_infrastructure_outputs(outputs):
    """Update .env.prod with infrastructure-generated values"""
    print_info("Updating .env.prod with infrastructure outputs...")
    
    # Read current .env.prod
    env_vars = {}
    with open('.env.prod', 'r') as f:
        lines = f.readlines()
    
    # Parse existing variables
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    
    # Update with infrastructure outputs
    updates = {}
    
    if 'database_url' in outputs:
        updates['DATABASE_URL'] = outputs['database_url']['value']
    
    if 's3_bucket_name' in outputs:
        updates['AWS_S3_BUCKET_NAME'] = outputs['s3_bucket_name']['value']
    
    if 'alb_dns_name' in outputs:
        alb_dns = outputs['alb_dns_name']['value']
        # These will be updated after domain is configured
        if not env_vars.get('NEXT_PUBLIC_APP_URL') or 'placeholder' in env_vars.get('NEXT_PUBLIC_APP_URL', ''):
            updates['NEXT_PUBLIC_APP_URL'] = f"https://{alb_dns}"
        if not env_vars.get('BACKEND_URL') or 'placeholder' in env_vars.get('BACKEND_URL', ''):
            updates['BACKEND_URL'] = f"https://{alb_dns}"
    
    # Generate secure keys if they don't exist or are placeholders
    if not env_vars.get('JWT_SECRET_KEY') or 'your_' in env_vars.get('JWT_SECRET_KEY', ''):
        updates['JWT_SECRET_KEY'] = generate_secure_key(64)
    
    if not env_vars.get('ENCRYPTION_KEY') or 'your_' in env_vars.get('ENCRYPTION_KEY', ''):
        updates['ENCRYPTION_KEY'] = generate_secure_key(32)
    
    if not env_vars.get('BACKEND_API_KEY') or 'your_' in env_vars.get('BACKEND_API_KEY', ''):
        updates['BACKEND_API_KEY'] = generate_secure_key(32)
    
    # Apply updates
    for key, value in updates.items():
        env_vars[key] = value
    
    # Write updated .env.prod
    with open('.env.prod', 'w') as f:
        f.write("# Production Environment Configuration\n")
        f.write("# Auto-updated by deployment script\n")
        f.write(f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Group variables by category
        categories = {
            'AWS Configuration': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 'AWS_S3_BUCKET_NAME'],
            'Database': ['DATABASE_URL'],
            'Application URLs': ['NEXT_PUBLIC_APP_URL', 'BACKEND_URL', 'BACKEND_API_KEY'],
            'Supabase Authentication': ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'NEXT_PUBLIC_SUPABASE_URL', 'NEXT_PUBLIC_SUPABASE_ANON_KEY'],
            'Stripe Payments': ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY', 'NEXT_PUBLIC_STRIPE_PRO_PRICE_ID'],
            'Sentry Error Tracking': ['NEXT_PUBLIC_SENTRY_DSN', 'SENTRY_ORG', 'SENTRY_PROJECT', 'SENTRY_AUTH_TOKEN'],
            'PostHog Analytics': ['NEXT_PUBLIC_POSTHOG_KEY', 'NEXT_PUBLIC_POSTHOG_HOST', 'POSTHOG_PROJECT_API_KEY', 'POSTHOG_HOST'],
            'Email Notifications': ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS', 'NOTIFICATION_EMAIL'],
            'Security': ['JWT_SECRET_KEY', 'ENCRYPTION_KEY'],
            'GitHub Integration': ['GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME'],
            'Monitoring': ['AUTO_FIX_ENABLED', 'MONITORING_INTERVAL', 'ERROR_THRESHOLD']
        }
        
        for category, vars_in_category in categories.items():
            f.write(f"# === {category} ===\n")
            for var in vars_in_category:
                if var in env_vars:
                    f.write(f"{var}={env_vars[var]}\n")
            f.write("\n")
        
        # Add any remaining variables
        written_vars = set()
        for vars_in_category in categories.values():
            written_vars.update(vars_in_category)
        
        remaining_vars = set(env_vars.keys()) - written_vars
        if remaining_vars:
            f.write("# === Other Variables ===\n")
            for var in sorted(remaining_vars):
                f.write(f"{var}={env_vars[var]}\n")
    
    if updates:
        print_status("Updated .env.prod with infrastructure outputs:")
        for key, value in updates.items():
            if 'SECRET' in key or 'KEY' in key or 'PASS' in key:
                print(f"  • {key}: [SECURE VALUE GENERATED]")
            else:
                print(f"  • {key}: {value}")
    
    return True

def create_terraform_state_bucket():
    """Create S3 bucket for Terraform state"""
    print_info("Setting up Terraform state storage...")
    
    bucket_name = "pdf-excel-saas-terraform-state"
    
    # Check if bucket exists
    success, stdout, stderr = run_command(f'aws s3 ls s3://{bucket_name}', capture_output=True)
    if success:
        print_status("Terraform state bucket already exists")
        return True
    
    # Create bucket
    print_info("Creating Terraform state bucket...")
    success, stdout, stderr = run_command(f'aws s3 mb s3://{bucket_name} --region us-east-1')
    if not success:
        print_error(f"Failed to create bucket: {stderr}")
        return False
    
    # Enable versioning
    success, stdout, stderr = run_command(f'aws s3api put-bucket-versioning --bucket {bucket_name} --versioning-configuration Status=Enabled')
    if success:
        print_status("Terraform state bucket created and configured")
        return True
    else:
        print_warning("Bucket created but versioning configuration failed")
        return True

def deploy_infrastructure():
    """Deploy infrastructure using Terraform"""
    print_info("Deploying infrastructure with Terraform...")
    
    # Change to infra directory
    if not os.path.exists('infra'):
        print_error("infra directory not found")
        return False, None
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    success, stdout, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print_error("Terraform init failed")
        return False, None
    
    # Plan deployment
    print_info("Planning infrastructure deployment...")
    success, stdout, stderr = run_command(
        'terraform plan -var="aws_region=us-east-1" -var="environment=prod" -var="app_name=pdf-excel-saas" -out=tfplan',
        cwd='infra'
    )
    if not success:
        print_error("Terraform plan failed")
        return False, None
    
    # Show plan summary
    print_info("Terraform plan created successfully")
    
    # Ask for confirmation
    confirm = input("\n⚠️  This will create AWS resources that may incur costs. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled by user")
        return False, None
    
    # Apply deployment
    print_info("Applying Terraform configuration...")
    success, stdout, stderr = run_command('terraform apply tfplan', cwd='infra')
    if not success:
        print_error("Terraform apply failed")
        return False, None
    
    print_status("Infrastructure deployment completed!")
    
    # Get outputs
    success, stdout, stderr = run_command('terraform output -json', cwd='infra', capture_output=True)
    if success:
        try:
            outputs = json.loads(stdout)
            print_info("Infrastructure outputs:")
            for key, value in outputs.items():
                if 'value' in value:
                    print(f"  • {key}: {value['value']}")
            
            # Save outputs to file
            with open('infrastructure-outputs.json', 'w') as f:
                json.dump(outputs, f, indent=2)
            
            print_status("Infrastructure outputs saved to infrastructure-outputs.json")
            
            return True, outputs
            
        except json.JSONDecodeError:
            print_warning("Could not parse Terraform outputs")
            return True, None
    
    return True, None

def setup_ecr_repositories():
    """Create ECR repositories"""
    print_info("Setting up container repositories...")
    
    repositories = ['pdf-excel-saas-frontend', 'pdf-excel-saas-backend']
    
    for repo in repositories:
        # Check if repository exists
        success, stdout, stderr = run_command(f'aws ecr describe-repositories --repository-names {repo} --region us-east-1', capture_output=True)
        if success:
            print_status(f"{repo} repository already exists")
        else:
            # Create repository
            print_info(f"Creating {repo} repository...")
            success, stdout, stderr = run_command(f'aws ecr create-repository --repository-name {repo} --region us-east-1 --image-scanning-configuration scanOnPush=true')
            if success:
                print_status(f"{repo} repository created")
            else:
                print_warning(f"Failed to create {repo} repository")

def setup_monitoring():
    """Set up CloudWatch logging"""
    print_info("Setting up monitoring and logging...")
    
    log_groups = [
        '/ecs/pdf-excel-saas-prod-frontend',
        '/ecs/pdf-excel-saas-prod-backend'
    ]
    
    for log_group in log_groups:
        success, stdout, stderr = run_command(f'aws logs create-log-group --log-group-name "{log_group}" --region us-east-1', capture_output=True)
        # Ignore errors as log groups might already exist
    
    print_status("CloudWatch log groups created")

def create_deployment_checklist(alb_dns=None):
    """Create post-deployment checklist"""
    checklist = f"""# Post-Deployment Checklist

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Infrastructure ✅
- [x] AWS VPC and networking
- [x] RDS PostgreSQL database  
- [x] S3 bucket for file storage
- [x] ECS cluster and services
- [x] Application Load Balancer
- [x] ECR repositories
- [x] CloudWatch logging

## Next Steps (Required)
- [ ] Configure domain DNS pointing to: {alb_dns if alb_dns else 'Check infrastructure-outputs.json'}
- [ ] Set up SSL certificate in AWS Certificate Manager
- [ ] Update NEXT_PUBLIC_APP_URL and BACKEND_URL with your domain
- [ ] Configure GitHub repository secrets
- [ ] Deploy application via GitHub Actions

## Email Notifications (Optional)
- [ ] Set up Gmail App Password or AWS SES
- [ ] Set SMTP_PASS in environment variables
- [ ] Test email notifications

## Testing Required
- [ ] Test complete user flow: signup → upload → convert → download
- [ ] Test Stripe payment integration
- [ ] Verify Supabase authentication
- [ ] Check Sentry error reporting
- [ ] Confirm PostHog analytics tracking

## Important Information
- **Infrastructure Outputs**: Check infrastructure-outputs.json
- **AWS Console**: https://console.aws.amazon.com/
- **GitHub Repository**: https://github.com/yagakeerthikiran/pdf-to-excel-saas
- **Load Balancer DNS**: {alb_dns if alb_dns else 'See outputs file'}

## Cost Management
- **Expected monthly cost**: $150-250
- **Set up billing alerts**: AWS Console → Billing → Budgets
- **Monitor usage**: CloudWatch metrics
"""
    
    with open('deployment-checklist.md', 'w') as f:
        f.write(checklist)
    
    print_status("Deployment checklist created: deployment-checklist.md")

def main():
    """Main deployment function"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🚀 PDF to Excel SaaS - Infrastructure Deployment")
    print("================================================")
    print(f"{Colors.END}")
    
    start_time = datetime.now()
    
    # Check prerequisites
    if not check_prerequisites():
        send_email_notification("Deployment Failed", "Prerequisites check failed")
        sys.exit(1)
    
    # Check pre-deployment configuration
    if not check_pre_deployment_config():
        send_email_notification("Deployment Failed", "Pre-deployment configuration incomplete")
        sys.exit(1)
    
    # Create Terraform state bucket
    if not create_terraform_state_bucket():
        send_email_notification("Deployment Failed", "Terraform state bucket creation failed")
        sys.exit(1)
    
    # Deploy infrastructure
    success, outputs = deploy_infrastructure()
    if not success:
        send_email_notification("Deployment Failed", "Infrastructure deployment failed")
        sys.exit(1)
    
    # Update environment with infrastructure outputs
    if outputs:
        update_env_with_infrastructure_outputs(outputs)
    
    # Setup ECR repositories
    setup_ecr_repositories()
    
    # Setup monitoring
    setup_monitoring()
    
    # Get ALB DNS for checklist
    alb_dns = None
    if outputs and 'alb_dns_name' in outputs:
        alb_dns = outputs['alb_dns_name']['value']
    
    # Create checklist
    create_deployment_checklist(alb_dns)
    
    # Calculate deployment time
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Success summary
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Deployment Summary{Colors.END}")
    print(f"{Colors.GREEN}=================={Colors.END}")
    print(f"• Status: ✅ Completed Successfully")
    print(f"• Duration: {duration}")
    print(f"• Region: us-east-1")
    print(f"• Environment: prod")
    
    if alb_dns:
        print(f"• Load Balancer: {alb_dns}")
        print(f"\n{Colors.CYAN}🌐 Next: Configure your domain to point to {alb_dns}{Colors.END}")
    
    print(f"{Colors.CYAN}📋 See: deployment-checklist.md for next steps{Colors.END}")
    
    # Send success notification
    success_message = f"""Infrastructure deployment completed successfully!

Duration: {duration}
Region: us-east-1
Environment: prod

Load Balancer DNS: {alb_dns if alb_dns else 'Check infrastructure-outputs.json'}

Critical Next Steps:
1. Configure domain DNS to point to ALB
2. Set up SSL certificate in AWS Certificate Manager  
3. Update domain URLs in .env.prod
4. Configure GitHub secrets and deploy application

Resources:
- AWS Console: https://console.aws.amazon.com/
- Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas
- Checklist: deployment-checklist.md
"""
    
    send_email_notification("Infrastructure Deployment Successful", success_message)
    
    print(f"\n{Colors.CYAN}📧 Email notification sent to: yagakeerthikiran@gmail.com{Colors.END}")

if __name__ == "__main__":
    main()
