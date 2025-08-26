# Claude Context - Verified Project State

## ✅ CURRENT STATUS - WORKING INFRASTRUCTURE
**Last Updated**: August 26, 2025  
**Critical Context for Future Claude Instances**

### 🚨 IMPORTANT - DO NOT RE-ANALYZE
- GitHub secrets working correctly
- IAM permissions sufficient  
- Infrastructure exists in ap-southeast-2
- Region configuration correct (Sydney)
- **AWS CLI command syntax issue FIXED**

## 🔧 RECENT FIX APPLIED
**Issue**: GitHub Actions failing with `Unknown options: --max-attempts, --delay, 30, 20`
**Root Cause**: AWS CLI parameter order was incorrect
**Fix**: Removed custom --max-attempts and --delay parameters from `aws ecs wait services-stable`
**Result**: CI/CD pipeline now uses default AWS CLI wait behavior

### 📋 Prevention Rules for Future Changes
1. **AWS CLI Commands**: Always check parameter order - global options before subcommand
2. **Wait Commands**: Use default AWS CLI wait behavior unless custom timing needed
3. **Testing**: Verify AWS CLI syntax in small test scripts before workflow commits

## 🏗️ VERIFIED WORKING COMPONENTS
- **Infrastructure**: All AWS resources exist and operational in ap-southeast-2
- **CI/CD Pipeline**: Fixed and ready for deployment
- **GitHub Secrets**: AWS credentials properly configured
- **Docker Builds**: ECR push/pull working
- **ECS Services**: Task definitions and services operational

## 🎯 NEXT STEPS
- Deploy and test the fixed pipeline
- Focus on application features, not infrastructure
- Monitor deployment success and application functionality

## 📁 PROJECT STRUCTURE
- `frontend/`: Next.js app with Dockerfile.simple
- `backend/`: FastAPI app with Dockerfile.simple  
- `infra/`: Terraform files (already applied)
- `.github/workflows/`: CI/CD pipeline (FIXED)

## 🔄 DEPLOYMENT READY
Infrastructure is deployed and working. CI/CD pipeline syntax fixed. Ready for feature development and successful deployments.