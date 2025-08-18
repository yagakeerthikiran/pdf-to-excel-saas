def deploy_infrastructure():
    """Deploy infrastructure with Terraform (resume-safe)"""
    print_title("Deploying Infrastructure with Terraform")
    
    if not Path('infra').exists():
        print_error("infra directory not found")
        return False
    
    # Initialize Terraform with migration handling
    print_info("Initializing Terraform...")
    
    # Try normal init first
    success, _, stderr = run_command('terraform init', cwd='infra', check=False)
    
    if not success and "Backend configuration changed" in stderr:
        print_warning("Backend configuration changed, attempting migration...")
        success, _, _ = run_command('terraform init -migrate-state', cwd='infra', check=False)
        
        if not success:
            print_warning("Migration failed, reconfiguring backend...")
            success, _, _ = run_command('terraform init -reconfigure', cwd='infra')
    
    if not success:
        print_error("Terraform init failed")
        return False
    
    print_status("Terraform initialized successfully")
    
    # Plan deployment
    print_info("Planning infrastructure deployment...")
    success, _, _ = run_command(
        f'terraform plan '
        f'-var="aws_region={AWS_REGION}" '
        f'-var="environment={ENVIRONMENT}" '
        f'-var="app_name={APP_NAME}" '
        f'-out=tfplan',
        cwd='infra'
    )
    
    if not success:
        print_error("Terraform plan failed")
        return False
    
    # Show plan summary
    print_info("Terraform plan summary:")
    success, stdout, _ = run_command(
        'terraform show -no-color tfplan',
        capture=True,
        cwd='infra',
        check=False
    )
    
    if stdout:
        # Extract plan summary
        lines = stdout.split('\n')
        for line in lines:
            if 'Plan:' in line or 'will be created' in line or 'will be updated' in line or 'will be destroyed' in line:
                print(line)
    
    # Confirm deployment
    print(f"\n{Colors.YELLOW}⚠️  This will create AWS resources in Sydney ({AWS_REGION}) that may incur costs.{Colors.END}")
    confirm = input("Do you want to proceed with the deployment? (y/N): ")
    
    if confirm.lower() != 'y':
        print_warning("Deployment cancelled by user")
        return False
    
    # Apply configuration
    print_info("Applying Terraform configuration...")
    success, _, _ = run_command('terraform apply tfplan', cwd='infra')
    
    if success:
        print_status("Infrastructure deployment completed!")
        capture_terraform_outputs()
        return True
    else:
        print_error("Infrastructure deployment failed!")
        return False