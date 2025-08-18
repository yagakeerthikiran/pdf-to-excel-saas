# Quick Deployment Guide - Sydney Region

This guide focuses on the **actively used** deployment scripts for the PDF to Excel SaaS infrastructure in Sydney (ap-southeast-2).

## 🎯 Active Scripts Overview

### Main Deployment Script
- **`scripts/deploy-infrastructure.py`** - Primary deployment script (resume-safe, Sydney-focused)
- **`scripts/validate_env.py`** - Environment validation (used by main script)

### Environment Configuration
- **`.env.prod.template`** - Production environment template (Sydney region)
- **`env.schema.json`** - Validation schema (enforces Sydney region)

### Infrastructure
- **`infra/main.tf`** - Complete Terraform configuration (defaults to Sydney)

## 🚀 Quick Start (Windows)

### 1. Prerequisites
```bash
# Install required tools
# - AWS CLI: https://aws.amazon.com/cli/
# - Terraform: https://terraform.io/downloads
# - Python 3: https://python.org/
# - Docker: https://docker.com/ (optional)

# Configure AWS credentials
aws configure
# Use ap-southeast-2 as default region
```

### 2. One-Command Deployment
```bash
# From project root directory
python scripts/deploy-infrastructure.py
```

## 📋 What the Script Does

### ✅ Automated Steps
• **Prerequisites check** - Validates AWS CLI, Terraform, Python
• **Environment validation** - Creates/validates .env.prod file
• **Terraform state bucket** - Creates S3 bucket for remote state
• **Infrastructure deployment** - Deploys complete AWS infrastructure
• **ECR repositories** - Creates container registries
• **Docker login** - Authenticates with ECR
• **Output capture** - Saves deployment results

### 🎯 Sydney Region Focus
• All resources deployed to **ap-southeast-2**
• Environment template defaults to Sydney
• Validation enforces Sydney region only
• Cost-optimized for Australian workloads

## 📁 Key Output Files

After successful deployment:
- `infrastructure-outputs.json` - All Terraform outputs
- `infrastructure-outputs.env` - Environment variables format
- `deployment-summary.md` - Next steps and commands
- `.env.prod` - Production environment configuration

## 🔧 Dependencies Used By Main Script

The main Python script (`deploy-infrastructure.py`) depends on:

1. **`scripts/validate_env.py`** - Environment validation
2. **`env.schema.json`** - Validation rules
3. **`.env.prod.template`** - Environment template
4. **`infra/main.tf`** - Terraform infrastructure

## 🚨 Important Notes

### Resume-Safe Design
• Script can be run multiple times safely
• Checks existing resources before creating
• Uses unique S3 bucket names with account ID
• Terraform state management included

### Security
• Never commits .env.prod (gitignored)
• Uses strong encryption for state bucket
• IAM roles follow least privilege principle
• All secrets properly managed

### Cost Optimization
• Uses t3.micro for RDS (free tier eligible)
• Minimal ECS containers (256 CPU, 512 MB)
• S3 lifecycle policies for cost management
• CloudWatch log retention set to 7 days

## 🔄 Resume Failed Deployment

If deployment fails or is interrupted:

```bash
# Just run the script again - it's resume-safe
python scripts/deploy-infrastructure.py
```

The script will:
• Skip already created resources
• Continue from the last successful step
• Validate existing configuration
• Complete any remaining tasks

## 📞 Troubleshooting

### Common Issues
1. **AWS credentials not configured** → Run `aws configure`
2. **Wrong region** → Ensure ap-southeast-2 in AWS config
3. **Terraform state conflicts** → Script handles automatically
4. **Missing .env.prod** → Script creates from template

### Getting Help
• Check `deployment-summary.md` for detailed guidance
• Review AWS Console in Sydney region
• Validate environment with: `python scripts/validate_env.py --env production`

## 🎉 Next Steps After Deployment

1. **Build & Push Images**
   ```bash
   # Commands will be in deployment-summary.md
   ```

2. **Configure GitHub Secrets**
   ```bash
   # Use scripts/setup-github-secrets.ps1 if needed
   ```

3. **Test Application**
   ```bash
   # Load balancer URL in infrastructure-outputs.json
   ```

---

**Note**: This deployment focuses on the actively used scripts only. Other scripts in the repository are available but not part of the main deployment flow.