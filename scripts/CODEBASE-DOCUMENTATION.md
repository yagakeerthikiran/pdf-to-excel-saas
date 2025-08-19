# PDF to Excel SaaS - Codebase Documentation

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

## 🚀 Key Scripts & Commands

### Core Deployment Scripts
```bash
# Main deployment (production)
python scripts/deploy-infrastructure.py

# Environment validation
python scripts/validate_env.py

# Environment generator/troubleshooter
python scripts/generate-env-vars.py

# Infrastructure diagnostics
python scripts/diagnose-infrastructure.py

# Safe infrastructure destruction
python scripts/destroy-infrastructure.py
```

### Development Commands
```bash
# Frontend development
cd frontend && npm run dev

# Backend development  
cd backend && uvicorn main:app --reload

# Local testing
docker-compose up --build
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

### Terraform State
- State stored in S3 backend
- DynamoDB table for state locking
- Encryption at rest enabled

## 🔧 Common Issues & Solutions

### Import Errors in Python Scripts
**Issue**: `NameError: name 'time' is not defined`
**Solution**: Always include required imports at script top:
```python
import subprocess
import json
import sys
import time
from pathlib import Path
```

### AWS Region Consistency
**Issue**: Resources created in wrong region
**Solution**: All scripts use `AWS_REGION = "ap-southeast-2"`
- Verify AWS CLI region: `aws configure get region`
- Scripts override with `--region ap-southeast-2`

### Terraform State Issues
**Issue**: State file corruption or conflicts
**Solution**: 
```bash
# Refresh state
terraform refresh

# Import existing resources
terraform import aws_s3_bucket.main bucket-name

# Reset state (dangerous)
terraform state rm resource.name
```

### Docker Build Failures
**Issue**: Platform compatibility errors
**Solution**: 
```bash
# Build for AMD64 (AWS ECS)
docker build --platform linux/amd64 .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 .
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

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows
```yaml
# .github/workflows/deploy.yml
- Build frontend/backend images
- Push to ECR
- Deploy to ECS
- Run health checks
```

### Deployment Process
1. Code push triggers GitHub Action
2. Docker images built and pushed to ECR
3. ECS services updated with new images
4. Health checks verify deployment
5. Rollback on failure

## 📊 Monitoring & Observability

### Sentry (Error Tracking)
- Frontend: React error boundary
- Backend: FastAPI middleware
- Real-time error alerts

### PostHog (Analytics)
- User behavior tracking
- Feature usage metrics
- Conversion funnel analysis

### CloudWatch (Infrastructure)
- Container logs and metrics
- RDS performance insights
- Custom dashboards

## 🧪 Testing Strategy

### Local Testing
```bash
# Unit tests
cd backend && pytest
cd frontend && npm test

# Integration tests
docker-compose -f docker-compose.test.yml up

# End-to-end tests
cd frontend && npm run test:e2e
```

### Production Validation
```bash
# Health checks
curl https://api.your-domain.com/health

# Database connectivity
python scripts/diagnose-infrastructure.py

# Full system test
python scripts/validate_env.py
```

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] AWS credentials valid
- [ ] Docker images built successfully
- [ ] Database migrations ready
- [ ] SSL certificates valid

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

### Current State
- **Branch**: `feat/infrastructure-clean`
- **Status**: Infrastructure deployment in progress
- **Region**: ap-southeast-2 (Sydney)
- **Environment**: Production-ready configuration

---

*Last Updated: August 2025*
*For questions, create GitHub issue or contact development team*
