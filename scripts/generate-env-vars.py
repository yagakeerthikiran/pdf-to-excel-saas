#!/usr/bin/env python3
"""
Environment Variable Generator & Troubleshooter
Helps generate missing environment variables and troubleshoot deployment issues
"""

import os
import sys
import subprocess
import json
import secrets
import string
import re
from datetime import datetime
from pathlib import Path

AWS_REGION = "ap-southeast-2"
APP_NAME = "pdf-excel-saas"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(msg): 
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_warning(msg): 
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_error(msg): 
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg): 
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def print_title(msg):
    print(f"\n{Colors.BLUE}🚀 {msg}{Colors.END}")
    print("=" * (len(msg) + 4))

def run_command(cmd, capture=True, cwd=None):
    """Run command with error handling"""
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, cwd=cwd)
    return result.returncode == 0, result.stdout, result.stderr

def validate_env_format(key, value):
    """Validate environment variable format using improved patterns"""
    errors = []
    
    # Validation patterns (more flexible than schema)
    patterns = {
        'AWS_ACCESS_KEY_ID': {
            'pattern': r'^(AKIA|ASIA)[0-9A-Z]{16}$',
            'desc': 'AWS Access Key ID format (AKIA for long-term, ASIA for temporary)'
        },
        'GITHUB_TOKEN': {
            'pattern': r'^(ghp_|github_pat_|ghs_)[a-zA-Z0-9_]{20,}$',
            'desc': 'Valid GitHub Personal Access Token'
        },
        'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY': {
            'pattern': r'^pk_(test_|live_)[0-9a-zA-Z]{20,}$',
            'desc': 'Valid Stripe publishable key format'
        },
        'STRIPE_SECRET_KEY': {
            'pattern': r'^sk_(test_|live_)[0-9a-zA-Z]{20,}$',
            'desc': 'Valid Stripe secret key format'
        },
        'STRIPE_WEBHOOK_SECRET': {
            'pattern': r'^whsec_[0-9a-zA-Z]{20,}$',
            'desc': 'Valid Stripe webhook secret format'
        },
        'SUPABASE_URL': {
            'pattern': r'^https://[a-zA-Z0-9][a-zA-Z0-9\.-]*\.(supabase\.co|localhost|127\.0\.0\.1).*$',
            'desc': 'Valid Supabase project URL'
        },
        'DATABASE_URL': {
            'pattern': r'^postgresql://.*',
            'desc': 'PostgreSQL connection string'
        }
    }
    
    if key in patterns:
        pattern_info = patterns[key]
        if not re.match(pattern_info['pattern'], value):
            errors.append(f"❌ {key}: Invalid format. {pattern_info['desc']}")
    
    # Check for obvious placeholder values
    placeholder_patterns = [
        r'^your_.*',
        r'^.*_your_.*',
        r'^.*placeholder.*',
        r'^example.*',
        r'^test.*key.*',
        r'^sk_test_.*placeholder.*'
    ]
    
    for pattern in placeholder_patterns:
        if re.match(pattern, value, re.IGNORECASE):
            errors.append(f"⚠️  {key}: Appears to be a placeholder value")
            break
    
    return errors

def validate_environment_file(env_file):
    """Validate environment file and show results"""
    print_title(f"Validating Environment File: {env_file}")
    
    if not os.path.exists(env_file):
        print_error(f"Environment file not found: {env_file}")
        return False
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' not in line:
                print_warning(f"Invalid line format at line {line_num}: {line}")
                continue
            
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    
    print_info(f"Found {len(env_vars)} environment variables")
    
    # Validate each variable
    all_errors = []
    for key, value in env_vars.items():
        if not value or value.strip() == '':
            all_errors.append(f"⚠️  {key}: Empty value")
            continue
        
        errors = validate_env_format(key, value)
        all_errors.extend(errors)
    
    # Print results
    if all_errors:
        print("\n🚨 VALIDATION ERRORS:")
        for error in all_errors:
            print(f"  {error}")
        return False
    else:
        print_status("All environment variables passed validation!")
        return True

def check_current_directory():
    """Check if we're in the right directory"""
    print_title("Checking Current Directory")
    
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    required_files = ['README.md', 'scripts/deploy-infrastructure.py', 'infra/main.tf']
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print_status(f"Found: {file_path}")
        else:
            print_error(f"Missing: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print_error("You're not in the project root directory!")
        print_info("Please navigate to C:\\AI\\GIT_Repos\\pdf-to-excel-saas")
        return False
    
    return True

def check_deployment_outputs():
    """Check for existing deployment outputs"""
    print_title("Checking for Deployment Outputs")
    
    output_files = [
        'infrastructure-outputs.json',
        'infrastructure-outputs.env', 
        'deployment-summary.md',
        '.env.prod'
    ]
    
    found_files = []
    
    for file_path in output_files:
        if os.path.exists(file_path):
            print_status(f"Found: {file_path}")
            found_files.append(file_path)
        else:
            print_warning(f"Missing: {file_path}")
    
    return found_files

def extract_terraform_outputs():
    """Extract outputs from Terraform state"""
    print_title("Extracting Terraform Outputs")
    
    if not os.path.exists('infra'):
        print_error("infra directory not found")
        return None
    
    # Check if Terraform is initialized
    if not os.path.exists('infra/.terraform'):
        print_warning("Terraform not initialized")
        print_info("Run: cd infra && terraform init")
        return None
    
    outputs = {}
    output_keys = [
        'alb_dns_name',
        's3_bucket_name', 
        'ecr_frontend_url',
        'ecr_backend_url',
        'database_endpoint',
        'database_url',
        'vpc_id',
        'ecs_cluster_name'
    ]
    
    print_info("Extracting Terraform outputs...")
    
    for key in output_keys:
        success, stdout, stderr = run_command(f'terraform output -raw {key}', cwd='infra')
        
        if success and stdout.strip():
            outputs[key] = stdout.strip()
            print_status(f"{key}: {outputs[key]}")
        else:
            outputs[key] = "N/A"
            print_warning(f"{key}: Not available")
    
    # Get AWS account info
    success, stdout, _ = run_command(f'aws sts get-caller-identity --region {AWS_REGION}')
    if success:
        account_info = json.loads(stdout)
        outputs['aws_account_id'] = account_info['Account']
        outputs['aws_region'] = AWS_REGION
    
    return outputs

def generate_missing_env_vars():
    """Generate missing environment variables"""
    print_title("Generating Missing Environment Variables")
    
    env_vars = {}
    
    # Generate BACKEND_API_KEY
    backend_api_key = secrets.token_urlsafe(32)
    env_vars['BACKEND_API_KEY'] = backend_api_key
    print_status(f"Generated BACKEND_API_KEY: {backend_api_key}")
    
    # Generate JWT_SECRET_KEY
    jwt_secret = secrets.token_urlsafe(32)
    env_vars['JWT_SECRET_KEY'] = jwt_secret
    print_status(f"Generated JWT_SECRET_KEY: {jwt_secret}")
    
    # Generate ENCRYPTION_KEY
    encryption_key = secrets.token_urlsafe(32)
    env_vars['ENCRYPTION_KEY'] = encryption_key
    print_status(f"Generated ENCRYPTION_KEY: {encryption_key}")
    
    return env_vars

def check_aws_resources():
    """Check AWS resources manually"""
    print_title("Checking AWS Resources")
    
    # Check S3 buckets
    success, stdout, _ = run_command(f'aws s3 ls --region {AWS_REGION}')
    if success:
        buckets = [line.split()[-1] for line in stdout.strip().split('\n') if 'pdf-excel-saas' in line]
        if buckets:
            print_status(f"Found S3 buckets: {', '.join(buckets)}")
        else:
            print_warning("No PDF Excel SaaS buckets found")
    
    # Check RDS instances
    success, stdout, _ = run_command(f'aws rds describe-db-instances --region {AWS_REGION}')
    if success:
        try:
            rds_data = json.loads(stdout)
            instances = [db['DBInstanceIdentifier'] for db in rds_data['DBInstances'] if 'pdf-excel-saas' in db['DBInstanceIdentifier']]
            if instances:
                print_status(f"Found RDS instances: {', '.join(instances)}")
                for db in rds_data['DBInstances']:
                    if 'pdf-excel-saas' in db['DBInstanceIdentifier']:
                        endpoint = db['Endpoint']['Address']
                        print_info(f"Database endpoint: {endpoint}")
            else:
                print_warning("No PDF Excel SaaS databases found")
        except:
            print_warning("Could not parse RDS output")
    
    # Check Load Balancers
    success, stdout, _ = run_command(f'aws elbv2 describe-load-balancers --region {AWS_REGION}')
    if success:
        try:
            elb_data = json.loads(stdout)
            load_balancers = [lb['LoadBalancerName'] for lb in elb_data['LoadBalancers'] if 'pdf-excel-saas' in lb['LoadBalancerName']]
            if load_balancers:
                print_status(f"Found Load Balancers: {', '.join(load_balancers)}")
                for lb in elb_data['LoadBalancers']:
                    if 'pdf-excel-saas' in lb['LoadBalancerName']:
                        dns_name = lb['DNSName']
                        print_info(f"Load Balancer DNS: {dns_name}")
            else:
                print_warning("No PDF Excel SaaS load balancers found")
        except:
            print_warning("Could not parse ELB output")

def create_env_prod_file(terraform_outputs=None, generated_vars=None):
    """Create or update .env.prod file"""
    print_title("Creating/Updating .env.prod File")
    
    if not os.path.exists('.env.prod.template'):
        print_error(".env.prod.template not found")
        return False
    
    # Read template
    with open('.env.prod.template', 'r') as f:
        template_content = f.read()
    
    # Create updated content
    updated_content = template_content
    
    # Replace with actual values if available
    if terraform_outputs:
        if terraform_outputs.get('alb_dns_name', 'N/A') != 'N/A':
            alb_dns = terraform_outputs['alb_dns_name']
            updated_content = updated_content.replace('https://pdftoexcel.yourapp.com', f'http://{alb_dns}')
            updated_content = updated_content.replace('https://api.pdftoexcel.yourapp.com', f'http://{alb_dns}/api')
        
        if terraform_outputs.get('database_url', 'N/A') != 'N/A':
            db_url = terraform_outputs['database_url']
            updated_content = updated_content.replace(
                'postgresql://dbadmin:****@pdf-excel-saas-prod-db.******.ap-southeast-2.rds.amazonaws.com:5432/pdfexcel',
                db_url
            )
        
        if terraform_outputs.get('s3_bucket_name', 'N/A') != 'N/A':
            bucket_name = terraform_outputs['s3_bucket_name']
            updated_content = updated_content.replace('pdf-excel-saas-prod', bucket_name)
    
    # Replace generated secrets
    if generated_vars:
        for key, value in generated_vars.items():
            if key == 'BACKEND_API_KEY':
                updated_content = updated_content.replace('your_secure_backend_api_key_32_chars_min', value)
            elif key == 'JWT_SECRET_KEY':
                updated_content = updated_content.replace('your_jwt_secret_key_at_least_32_characters_long_for_security', value)
            elif key == 'ENCRYPTION_KEY':
                updated_content = updated_content.replace('your_32_byte_encryption_key_for_data_protection', value)
    
    # Write to .env.prod
    with open('.env.prod', 'w') as f:
        f.write(updated_content)
    
    print_status(".env.prod file created/updated")
    
    # Show what still needs to be filled
    print_info("You still need to configure these services manually:")
    print("• Supabase: https://supabase.com/ (free tier)")
    print("• Stripe: https://stripe.com/ (free for testing)")
    print("• Sentry: https://sentry.io/ (free tier)")
    print("• PostHog: https://posthog.com/ (free tier)")
    print("• GitHub Token: GitHub Settings > Developer settings > Personal access tokens")
    
    return True

def show_manual_steps():
    """Show manual steps to get missing values"""
    print_title("Manual Steps for Missing Environment Variables")
    
    steps = {
        "GITHUB_TOKEN": [
            "1. Go to GitHub.com → Settings → Developer settings",
            "2. Click 'Personal access tokens' → 'Tokens (classic)'",
            "3. Click 'Generate new token (classic)'",
            "4. Select scopes: repo, workflow, write:packages",
            "5. Copy the token (starts with ghp_ or github_pat_)"
        ],
        "Supabase Variables": [
            "1. Go to https://supabase.com/ and create account",
            "2. Create new project (free tier)",
            "3. Go to Settings → API",
            "4. Copy 'URL' for SUPABASE_URL and NEXT_PUBLIC_SUPABASE_URL",
            "5. Copy 'anon public' key for NEXT_PUBLIC_SUPABASE_ANON_KEY",
            "6. Copy 'service_role secret' key for SUPABASE_SERVICE_ROLE_KEY"
        ],
        "Stripe Variables": [
            "1. Go to https://stripe.com/ and create account",
            "2. Get API keys from Dashboard → Developers → API keys",
            "3. Copy 'Publishable key' for NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
            "4. Copy 'Secret key' for STRIPE_SECRET_KEY",
            "5. Create webhook endpoint for STRIPE_WEBHOOK_SECRET",
            "6. Create product/price for NEXT_PUBLIC_STRIPE_PRO_PRICE_ID"
        ],
        "Sentry Variables": [
            "1. Go to https://sentry.io/ and create account",
            "2. Create new project",
            "3. Copy DSN for NEXT_PUBLIC_SENTRY_DSN",
            "4. Get organization slug for SENTRY_ORG", 
            "5. Get project name for SENTRY_PROJECT",
            "6. Create auth token for SENTRY_AUTH_TOKEN"
        ],
        "PostHog Variables": [
            "1. Go to https://posthog.com/ and create account",
            "2. Copy Project API Key for NEXT_PUBLIC_POSTHOG_KEY",
            "3. Copy Project API Key for POSTHOG_PROJECT_API_KEY",
            "4. Use https://us.i.posthog.com for NEXT_PUBLIC_POSTHOG_HOST"
        ]
    }
    
    for category, step_list in steps.items():
        print(f"\n{Colors.CYAN}{category}:{Colors.END}")
        for step in step_list:
            print(f"  {step}")

def main():
    """Main troubleshooting function"""
    print(f"{Colors.BLUE}")
    print("🔧 PDF to Excel SaaS - Environment Variable Generator & Troubleshooter")
    print("======================================================================")
    print(f"{Colors.END}")
    
    # Step 1: Check directory
    if not check_current_directory():
        sys.exit(1)
    
    # Step 2: Validate existing .env.prod if it exists
    if os.path.exists('.env.prod'):
        print_info("Found existing .env.prod file")
        if validate_environment_file('.env.prod'):
            print_status("Your .env.prod file looks good! No format issues found.")
            return
        else:
            print_warning("Your .env.prod file has some validation issues (shown above)")
    
    # Step 3: Check for deployment outputs
    found_files = check_deployment_outputs()
    
    # Step 4: Try to extract Terraform outputs
    terraform_outputs = extract_terraform_outputs()
    
    # Step 5: Check AWS resources manually
    check_aws_resources()
    
    # Step 6: Generate missing environment variables
    generated_vars = generate_missing_env_vars()
    
    # Step 7: Create/update .env.prod
    create_env_prod_file(terraform_outputs, generated_vars)
    
    # Step 8: Show manual steps
    show_manual_steps()
    
    # Final summary
    print_title("Summary")
    if terraform_outputs:
        print_status("Terraform outputs extracted successfully")
    else:
        print_warning("Terraform outputs not available - may need to run deployment first")
    
    print_status("Generated secure keys for BACKEND_API_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY")
    print_status(".env.prod file created/updated")
    
    print(f"\n{Colors.CYAN}📋 Next Steps:{Colors.END}")
    print("1. Edit .env.prod and replace placeholder values with real service credentials")
    print("2. Follow the manual steps above to get service API keys")
    print("3. Run validation: python scripts/validate_env.py --env production --file .env.prod")
    print("4. Run deployment script: python scripts/deploy-infrastructure.py")
    print("5. Check infrastructure-outputs.json for final URLs")

if __name__ == "__main__":
    main()
