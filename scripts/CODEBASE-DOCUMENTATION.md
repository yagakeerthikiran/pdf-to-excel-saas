# PDF to Excel SaaS - Enhanced Codebase Documentation

## 🎯 Project Overview
**PDF to Excel SaaS** - Convert PDF documents to Excel spreadsheets with high accuracy
- **Tech Stack**: Next.js + TypeScript frontend, Python FastAPI backend
- **Infrastructure**: AWS Sydney (ap-southeast-2), Terraform, Docker, ECS
- **Services**: Stripe payments, Supabase auth, Sentry monitoring, PostHog analytics

## 📁 Project Structure
```
pdf-to-excel-saas/
├── frontend/          # Next.js app
├── backend/           # FastAPI Python backend
├── infra/            # Terraform AWS infrastructure
├── scripts/          # Deployment & utility scripts
├── docs/             # Documentation
└── .github/          # CI/CD workflows
```

## 🚀 Enhanced Deployment Scripts

### 🧠 Intelligent Deploy Script (NEW)
`scripts/deploy-infrastructure.py` - **Smart AWS-aware deployment**

**Features:**
• **AWS Resource Discovery** - Scans existing resources directly via boto3
• **State Drift Analysis** - Compares AWS reality vs Terraform state
• **Auto-Reconciliation** - Imports orphaned resources, fixes stale state
• **Dynamic Operations** - Generates create/update/delete/recreate plans
• **Safe Deployment** - Confirms all changes before applying

**Usage:**
```bash
# Requires boto3: pip install boto3
python scripts/deploy-infrastructure.py

# The script will:
# 1. Discover existing AWS resources
# 2. Analyze Terraform state drift
# 3. Recommend reconciliation actions
# 4. Apply infrastructure changes safely
```

### 🔧 Other Core Scripts
```bash
# Environment validation
python scripts/validate_env.py

# Environment generator/troubleshooter
python scripts/generate-env-vars.py

# Infrastructure diagnostics
python scripts/diagnose-infrastructure.py

# Safe infrastructure destruction
python scripts/destroy-infrastructure.py
```

## ⚠️ CRITICAL FIXES THAT KEEP GETTING LOST

### 🔄 Recurring Import Issues
**PROBLEM**: Scripts lose essential imports during modifications, causing runtime errors

**PERMANENT SOLUTION**: Always verify these imports exist at the top of every Python script:

#### destroy-infrastructure.py MUST HAVE:
```python
import subprocess
import json
import sys
import time  # ← THIS GETS LOST! Required for time.time() in create_rds_snapshot()
from pathlib import Path
```

#### deploy-infrastructure.py MUST HAVE:
```python
import subprocess
import json
import sys
import time
import boto3  # ← Required for AWS resource discovery
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
```

### 🛡️ Automated Verification Script
**Created**: `scripts/verify-script-integrity.py` - Run this after ANY script modification

```python
#!/usr/bin/env python3
"""
Script Integrity Verifier - Prevents recurring import issues
Run this after ANY modification to deployment scripts
"""

import ast
import sys
from pathlib import Path

REQUIRED_IMPORTS = {
    'destroy-infrastructure.py': [
        'subprocess', 'json', 'sys', 'time', 'pathlib.Path'
    ],
    'deploy-infrastructure.py': [
        'subprocess', 'json', 'sys', 'time', 'boto3', 'pathlib.Path', 
        'typing.Dict', 'typing.List', 'dataclasses.dataclass'
    ],
    'validate_env.py': [
        'subprocess', 'json', 'sys', 'pathlib.Path'
    ]
}

def verify_script_imports(script_path):
    """Verify script has required imports"""
    try:
        with open(script_path, 'r') as f:
            tree = ast.parse(f.read())
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        return imports
    except Exception as e:
        return f"Error parsing {script_path}: {e}"

def main():
    errors = []
    scripts_dir = Path('scripts')
    
    for script_name, required in REQUIRED_IMPORTS.items():
        script_path = scripts_dir / script_name
        if not script_path.exists():
            errors.append(f"Missing script: {script_name}")
            continue
            
        imports = verify_script_imports(script_path)
        if isinstance(imports, str):  # Error message
            errors.append(imports)
            continue
            
        missing = [req for req in required if req not in imports]
        if missing:
            errors.append(f"{script_name} missing imports: {missing}")
    
    if errors:
        print("❌ SCRIPT INTEGRITY FAILURES:")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)
    else:
        print("✅ All scripts have required imports")

if __name__ == "__main__":
    main()
```

### 🔒 Git Pre-commit Hook (Recommended)
Create `.git/hooks/pre-commit` to run verification automatically:

```bash
#!/bin/bash
cd "$(git rev-parse --show-toplevel)"
python scripts/verify-script-integrity.py
if [ $? -ne 0 ]; then
    echo "❌ Script integrity check failed. Fix imports before committing."
    exit 1
fi
```

## ⚙️ Environment Configuration

### Required Environment Files
- `.env.prod` - Production environment (gitignored)
- `.env.local` - Local development (gitignored)
- `.env.prod.template` - Template for production vars

### Critical Environment Variables
```bash
# AWS Configuration
AWS_REGION=ap-southeast-2
AWS_ACCOUNT_ID=your-account-id

# Database
DATABASE_URL=postgresql://...
DB_PASSWORD=secure-password

# Services
STRIPE_SECRET_KEY=sk_live_...
SUPABASE_URL=https://...
SENTRY_DSN=https://...
POSTHOG_KEY=phc_...
```

## 🏗️ Infrastructure Details

### AWS Resources (Sydney Region)
- **ECS Cluster**: Container orchestration
- **Application Load Balancer**: Traffic distribution
- **RDS PostgreSQL**: Primary database
- **S3 Bucket**: File storage
- **ECR Repositories**: Container images
- **VPC + Subnets**: Network isolation

### Terraform State Management
- State stored in S3 backend
- DynamoDB table for state locking
- Encryption at rest enabled
- **Auto-reconciliation** for drift detection

## 🔧 Common Issues & Solutions

### Python Dependencies
**Issue**: `ModuleNotFoundError: No module named 'boto3'`
**Solution**: Install required packages:
```bash
pip install boto3 dataclasses typing
```

### Import Errors in Python Scripts
**Issue**: `NameError: name 'time' is not defined`
**Root Cause**: Import statements get lost during script modifications
**Prevention**: Always run `python scripts/verify-script-integrity.py` after changes
**Quick Fix**: 
```python
# Add to top of script if missing:
import time
```

### AWS Region Consistency
**Issue**: Resources created in wrong region
**Solution**: All scripts use `AWS_REGION = "ap-southeast-2"`
- Verify AWS CLI region: `aws configure get region`
- Scripts override with `--region ap-southeast-2`

### Terraform State Drift
**Issue**: State file out of sync with AWS reality
**Solution**: Use intelligent deploy script
```bash
python scripts/deploy-infrastructure.py
# This auto-detects and reconciles drift
```

### Docker Build Failures
**Issue**: Platform compatibility errors
**Solution**: 
```bash
# Build for AMD64 (AWS ECS)
docker build --platform linux/amd64 .
```

### ECS Deployment Hanging
**Issue**: Tasks fail to start or register
**Solution**:
1. Check task definition memory/CPU limits
2. Verify security group ports (80, 443, 8000)
3. Check CloudWatch logs for container errors
4. Ensure ECR image exists and is accessible

## 🚨 Critical Security Notes

### Secrets Management
- ❌ Never commit `.env` files to Git
- ✅ Use GitHub Secrets for CI/CD
- ✅ Rotate API keys if exposed
- ✅ Use AWS IAM roles for service access

### Stripe Integration
- Test keys: `pk_test_...` / `sk_test_...`
- Production keys: `pk_live_...` / `sk_live_...`
- Regenerate if committed to Git

### Database Security
- RDS in private subnets only
- SSL required for connections
- Regular automated backups
- Encryption at rest enabled

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Run `python scripts/verify-script-integrity.py`
- [ ] Environment variables configured
- [ ] AWS credentials valid (`aws sts get-caller-identity`)
- [ ] Python dependencies installed (`pip install boto3`)
- [ ] Docker images built successfully
- [ ] Database migrations ready

### Post-Deployment
- [ ] Health endpoints responding
- [ ] Database connections working
- [ ] File uploads functional
- [ ] Payment processing tested
- [ ] Monitoring alerts configured

## 🔧 Troubleshooting Guide

### Script Execution Issues
```bash
# PowerShell execution policy (Windows)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Python path issues
python -m scripts.deploy-infrastructure

# Permission errors (Linux/Mac)
chmod +x scripts/*.sh
```

### AWS CLI Issues
```bash
# Configure credentials
aws configure

# Test connectivity
aws sts get-caller-identity

# Set default region
aws configure set region ap-southeast-2
```

### Docker Issues
```bash
# Clear cache
docker system prune -a

# Check running containers
docker ps -a

# View logs
docker logs container-name
```

## 📝 Development Guidelines

### Code Style
- Python: Black formatter, type hints
- TypeScript: ESLint, Prettier
- Terraform: terraform fmt

### Git Workflow
- Main branch: `main` (production)
- Feature branches: `feat/feature-name`
- Infrastructure: `feat/infrastructure-clean`

### Commit Messages
```
feat: add PDF processing endpoint
fix: resolve database connection timeout
docs: update deployment instructions
refactor: optimize image processing pipeline
```

## 🆘 Emergency Procedures

### Production Outage
1. Check AWS Status Dashboard
2. Review CloudWatch alerts
3. Check ECS service health
4. Verify RDS availability
5. Review recent deployments

### Data Recovery
1. Identify backup timeframe
2. Create RDS snapshot
3. Restore from backup
4. Verify data integrity
5. Update application connections

### Security Incident
1. Rotate compromised credentials
2. Review access logs
3. Update security groups
4. Notify affected users
5. Document incident

## 📚 Additional Resources

### Documentation
- [AWS ECS Guide](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

### Support Contacts
- AWS Support: [Support Console](https://console.aws.amazon.com/support/)
- Stripe Support: [Stripe Dashboard](https://dashboard.stripe.com/)
- Sentry Support: [Sentry Help](https://sentry.io/support/)

---

## 🔄 Version History

### v1.0.0 - Initial Infrastructure
- Basic AWS setup with ECS
- Terraform infrastructure as code
- CI/CD pipeline with GitHub Actions
- Environment configuration templates

### v2.0.0 - Intelligent Deployment (Current)
- **Enhanced**: AWS resource discovery and state reconciliation
- **Fixed**: Recurring import issues with verification system
- **Added**: Comprehensive drift analysis and auto-remediation
- **Improved**: Documentation with permanent solutions

### Current State
- **Branch**: `feat/infrastructure-clean`
- **Status**: Enhanced infrastructure deployment ready
- **Region**: ap-southeast-2 (Sydney)
- **Environment**: Production-ready configuration

---

## 🛡️ IMPORTANT: To Prevent Recurring Issues

1. **Always run verification**: `python scripts/verify-script-integrity.py`
2. **Never modify scripts without testing imports**
3. **Use the intelligent deploy script for all infrastructure changes**
4. **Read this documentation before making changes**
5. **Set up the pre-commit hook for automatic verification**

*Last Updated: August 2025*
*For questions, create GitHub issue or contact development team*
