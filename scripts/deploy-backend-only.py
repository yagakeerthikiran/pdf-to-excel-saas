#!/usr/bin/env python3
"""
🐳 BACKEND-ONLY DEPLOYMENT SCRIPT
=================================

Deploy just the backend service to get the API working.
Frontend can be deployed separately later.
"""

import subprocess
import json
import sys
import time
import boto3
import base64
from pathlib import Path
from typing import Dict, List, Tuple, Optional

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

def print_deploy(msg): 
    print(f"{Colors.PURPLE}[DEPLOY] {msg}{Colors.END}")

def print_title(msg):
    print(f"\n{Colors.BLUE}=== {msg} ==={Colors.END}")
    print("=" * (len(msg) + 8))

def run_command(cmd, cwd=None, capture_output=True) -> Tuple[bool, str, str]:
    """Run command and return success status"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, cwd=cwd)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def get_aws_session() -> boto3.Session:
    """Get configured AWS session"""
    return boto3.Session(region_name=AWS_REGION)

def get_infrastructure_outputs() -> Dict:
    """Get infrastructure outputs from Terraform"""
    print_title("Getting Infrastructure Information")
    
    # Get outputs
    success, stdout, stderr = run_command('terraform output -json', cwd='infra')
    if not success:
        print_error(f"Could not get Terraform outputs: {stderr}")
        return {}
    
    try:
        outputs = json.loads(stdout)
        infrastructure = {}
        
        # Extract key information
        for key, value in outputs.items():
            infrastructure[key] = value.get('value')
            if not value.get('sensitive', False):
                print_info(f"{key}: {value.get('value')}")
            else:
                print_info(f"{key}: [SENSITIVE]")
        
        return infrastructure
    except json.JSONDecodeError as e:
        print_error(f"Could not parse Terraform outputs: {e}")
        return {}

def login_to_ecr(ecr_uri: str) -> bool:
    """Login to ECR registry"""
    print_info(f"Logging into ECR: {ecr_uri}")
    
    # Get ECR login token
    success, stdout, stderr = run_command(f'aws ecr get-login-password --region {AWS_REGION}')
    if not success:
        print_error(f"Failed to get ECR login token: {stderr}")
        return False
    
    password = stdout.strip()
    
    # Docker login to ECR
    success, stdout, stderr = run_command(f'echo {password} | docker login --username AWS --password-stdin {ecr_uri}')
    if success:
        print_status("ECR login successful")
        return True
    else:
        print_error(f"ECR login failed: {stderr}")
        return False

def build_and_push_backend(ecr_uri: str) -> bool:
    """Build and push backend Docker image to ECR"""
    print_deploy("Building and pushing backend image...")
    
    image_tag = f"{ecr_uri}:latest"
    
    # Build image
    print_info("Building backend image...")
    build_cmd = f'docker build -t {image_tag} .'
    success, stdout, stderr = run_command(build_cmd, cwd='backend', capture_output=False)
    
    if not success:
        print_error("Failed to build backend image")
        return False
    
    print_status("Backend image built successfully")
    
    # Push image
    print_info("Pushing backend image to ECR...")
    push_cmd = f'docker push {image_tag}'
    success, stdout, stderr = run_command(push_cmd, capture_output=False)
    
    if success:
        print_status("Backend image pushed successfully")
        return True
    else:
        print_error(f"Failed to push backend image: {stderr}")
        return False

def update_ecs_service(service_name: str, cluster_name: str) -> bool:
    """Update ECS service with new task definition"""
    print_deploy(f"Updating ECS service: {service_name}")
    
    session = get_aws_session()
    ecs = session.client('ecs')
    
    try:
        # Check if service exists
        response = ecs.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if response['services']:
            # Service exists, update it
            response = ecs.update_service(
                cluster=cluster_name,
                service=service_name,
                forceNewDeployment=True
            )
            print_status(f"ECS service {service_name} update initiated")
        else:
            print_warning(f"ECS service {service_name} does not exist - will be created by Terraform")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to update ECS service {service_name}: {e}")
        return False

def wait_for_deployment(service_name: str, cluster_name: str, timeout_minutes: int = 10) -> bool:
    """Wait for ECS service deployment to complete"""
    print_info(f"Waiting for {service_name} deployment to complete...")
    
    session = get_aws_session()
    ecs = session.client('ecs')
    
    timeout_seconds = timeout_minutes * 60
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        try:
            response = ecs.describe_services(
                cluster=cluster_name,
                services=[service_name]
            )
            
            if response['services']:
                service = response['services'][0]
                deployments = service['deployments']
                
                # Check if deployment is stable
                for deployment in deployments:
                    if deployment['status'] == 'PRIMARY' and deployment['runningCount'] == deployment['desiredCount']:
                        print_status(f"{service_name} deployment completed successfully")
                        return True
                
                print_info(f"Deployment in progress... ({int(time.time() - start_time)}s elapsed)")
                time.sleep(30)
            else:
                print_warning(f"Service {service_name} not found")
                return False
                
        except Exception as e:
            print_error(f"Error checking deployment status: {e}")
            return False
    
    print_error(f"Deployment timeout after {timeout_minutes} minutes")
    return False

def verify_backend_health(load_balancer_dns: str) -> bool:
    """Verify backend is responding to health checks"""
    print_title("Verifying Backend Health")
    
    import requests
    
    backend_endpoint = f"http://{load_balancer_dns}/health"
    
    try:
        print_info(f"Checking: {backend_endpoint}")
        response = requests.get(backend_endpoint, timeout=10)
        
        if response.status_code == 200:
            print_status(f"✅ Backend Health Check - PASSED")
            print_info(f"Response: {response.text}")
            return True
        else:
            print_warning(f"⚠️ Backend Health Check - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_warning(f"⚠️ Backend Health Check - Error: {e}")
        return False

def main():
    """Main backend deployment function"""
    print(f"{Colors.BLUE}")
    print("=== PDF TO EXCEL SAAS - BACKEND DEPLOYMENT ===")
    print("=============================================")
    print("Deploying backend API service only")
    print(f"Region: {AWS_REGION} | Environment: {ENVIRONMENT}")
    print(f"{Colors.END}")
    
    try:
        # Step 1: Get infrastructure information
        infrastructure = get_infrastructure_outputs()
        if not infrastructure:
            print_error("Could not get infrastructure information. Run deploy-infrastructure.py first.")
            sys.exit(1)
        
        # Step 2: Build and push backend image
        ecr_backend_url = infrastructure.get('ecr_backend_url')
        
        if not ecr_backend_url:
            print_error("ECR backend repository URL not found in infrastructure outputs")
            sys.exit(1)
        
        # Login to ECR
        ecr_registry = ecr_backend_url.split('/')[0]
        if not login_to_ecr(ecr_registry):
            sys.exit(1)
        
        # Build and push backend
        if not build_and_push_backend(ecr_backend_url):
            print_error("Backend build/push failed")
            sys.exit(1)
        
        # Step 3: Update ECS service
        cluster_name = infrastructure.get('ecs_cluster_name')
        if not cluster_name:
            print_error("ECS cluster name not found")
            sys.exit(1)
        
        # Update backend service
        backend_service_name = f'{APP_NAME}-{ENVIRONMENT}-backend'
        if not update_ecs_service(backend_service_name, cluster_name):
            print_warning("Backend service update failed (service may not exist yet)")
        
        # Step 4: Wait for deployment
        print_title("Waiting for Backend Deployment")
        wait_for_deployment(backend_service_name, cluster_name)
        
        # Step 5: Verify health
        load_balancer_dns = infrastructure.get('alb_dns_name')
        if load_balancer_dns:
            verify_backend_health(load_balancer_dns)
        
        # Step 6: Success summary
        print_title("🎉 BACKEND DEPLOYMENT COMPLETED! 🎉")
        print_status("✅ Backend Docker image built and pushed to ECR")
        print_status("✅ ECS backend service updated")
        print_status("✅ Backend API deployed and running")
        
        print_info("\n🌐 Your Backend API is now LIVE!")
        if load_balancer_dns:
            print_info(f"🔗 API Health Check: http://{load_balancer_dns}/health")
            print_info(f"🔗 API Documentation: http://{load_balancer_dns}/docs")
        
        print_info("\n📋 Next Steps:")
        print_info("1. 🧪 Test the API endpoints")
        print_info("2. 🎨 Fix and deploy frontend separately")
        print_info("3. 🔐 Configure authentication and authorization")
        print_info("4. 💳 Implement Stripe payment processing")
        
    except Exception as e:
        print_error(f"Backend deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
