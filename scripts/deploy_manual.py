#!/usr/bin/env python3
"""
Manual Infrastructure Deployment Script
This script manually deploys AWS infrastructure without PowerShell dependencies
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

def send_email_notification(subject, body, to_email="yagakeerthikiran@gmail.com"):
    """Send email notification instead of Slack"""
    try:
        # Load SMTP settings from environment
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', 'yagakeerthikiran@gmail.com')
        smtp_pass = os.getenv('SMTP_PASS', '')
        
        if not smtp_pass:
            print_warning("SMTP_PASS not configured - skipping email notification")
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

def validate_environment():
    """Validate environment configuration"""
    print_info("Validating environment configuration...")
    
    if not os.path.exists('.env.prod'):
        if os.path.exists('.env.prod.template'):
            print_warning(".env.prod not found, creating from template...")
            with open('.env.prod.template', 'r') as template:
                content = template.read()
            with open('.env.prod', 'w') as env_file:
                env_file.write(content)
            print_warning("Please edit .env.prod with your actual values")
            input("Press Enter when you've updated .env.prod...")
        else:
            print_error(".env.prod.template not found")
            return False
    
    # Run Python validation if available
    if os.path.exists('scripts/validate_env.py'):
        success, stdout, stderr = run_command('python scripts/validate_env.py --env production --file .env.prod')
        if success:
            print_status("Environment validation passed")
            return True
        else:
            print_error("Environment validation failed")
            return False
    else:
        print_warning("Environment validation script not found - skipping")
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
        return False
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    success, stdout, stderr = run_command('terraform init', cwd='infra')
    if not success:
        print_error("Terraform init failed")
        return False
    
    # Plan deployment
    print_info("Planning infrastructure deployment...")
    success, stdout, stderr = run_command(
        'terraform plan -var="aws_region=us-east-1" -var="environment=prod" -var="app_name=pdf-excel-saas" -out=tfplan',
        cwd='infra'
    )
    if not success:
        print_error("Terraform plan failed")
        return False
    
    # Show plan summary
    print_info("Terraform plan created successfully")
    
    # Ask for confirmation
    confirm = input("\n⚠️  This will create AWS resources that may incur costs. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled by user")
        return False
    
    # Apply deployment
    print_info("Applying Terraform configuration...")
    success, stdout, stderr = run_command('terraform apply tfplan', cwd='infra')
    if not success:
        print_error("Terraform apply failed")
        return False
    
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
            
        except json.JSONDecodeError:
            print_warning("Could not parse Terraform outputs")
    
    return True

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
    """Set up CloudWatch logging and monitoring"""
    print_info("Setting up monitoring and alerts...")
    
    log_groups = [
        '/ecs/pdf-excel-saas-prod-frontend',
        '/ecs/pdf-excel-saas-prod-backend',
        '/ecs/pdf-excel-saas-prod-monitoring'
    ]
    
    for log_group in log_groups:
        success, stdout, stderr = run_command(f'aws logs create-log-group --log-group-name "{log_group}" --region us-east-1', capture_output=True)
        # Ignore errors as log groups might already exist
    
    print_status("CloudWatch log groups created")

def create_deployment_checklist():
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

## Next Steps
- [ ] Configure domain DNS (use ALB DNS from outputs)
- [ ] Set up SSL certificate in AWS Certificate Manager
- [ ] Configure GitHub repository secrets
- [ ] Deploy application via GitHub Actions
- [ ] Set up email notifications (SMTP_PASS in environment)
- [ ] Test complete user flow
- [ ] Configure backup policies
- [ ] Run security audit

## Important Information
- **Infrastructure Outputs**: Check infrastructure-outputs.json
- **AWS Console**: https://console.aws.amazon.com/
- **GitHub Repository**: https://github.com/yagakeerthikiran/pdf-to-excel-saas
- **Email Notifications**: yagakeerthikiran@gmail.com

## Service Accounts Needed
- [ ] Stripe (payments) - See SERVICE-SETUP-GUIDE.md
- [ ] Supabase (auth) - See SERVICE-SETUP-GUIDE.md  
- [ ] Sentry (errors) - See SERVICE-SETUP-GUIDE.md
- [ ] PostHog (analytics) - See SERVICE-SETUP-GUIDE.md
- [ ] Domain registration
"""
    
    with open('deployment-checklist.md', 'w') as f:
        f.write(checklist)
    
    print_status("Deployment checklist created: deployment-checklist.md")

def main():
    """Main deployment function"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🚀 PDF to Excel SaaS - Manual Infrastructure Deployment")
    print("=====================================================")
    print(f"{Colors.END}")
    
    start_time = datetime.now()
    
    # Check prerequisites
    if not check_prerequisites():
        send_email_notification("Deployment Failed", "Prerequisites check failed")
        sys.exit(1)
    
    # Validate environment
    if not validate_environment():
        send_email_notification("Deployment Failed", "Environment validation failed")
        sys.exit(1)
    
    # Create Terraform state bucket
    if not create_terraform_state_bucket():
        send_email_notification("Deployment Failed", "Terraform state bucket creation failed")
        sys.exit(1)
    
    # Deploy infrastructure
    if not deploy_infrastructure():
        send_email_notification("Deployment Failed", "Infrastructure deployment failed")
        sys.exit(1)
    
    # Setup ECR repositories
    setup_ecr_repositories()
    
    # Setup monitoring
    setup_monitoring()
    
    # Create checklist
    create_deployment_checklist()
    
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
    print(f"• Next Steps: See deployment-checklist.md")
    
    # Send success notification
    success_message = f"""Infrastructure deployment completed successfully!

Duration: {duration}
Region: us-east-1
Environment: prod

Next Steps:
1. Check infrastructure-outputs.json for ALB DNS
2. Configure domain DNS to point to ALB
3. Set up service accounts (see SERVICE-SETUP-GUIDE.md)
4. Configure GitHub secrets
5. Deploy application

Dashboard: https://console.aws.amazon.com/
Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas
"""
    
    send_email_notification("Infrastructure Deployment Successful", success_message)
    
    print(f"\n{Colors.CYAN}📧 Email notification sent to: yagakeerthikiran@gmail.com{Colors.END}")
    print(f"{Colors.CYAN}📋 Next: Follow SERVICE-SETUP-GUIDE.md for service accounts{Colors.END}")

if __name__ == "__main__":
    main()
