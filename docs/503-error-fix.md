# 503 Error Fix Documentation

## Issues Fixed

### 1. Backend Container Import Error
**Problem**: `ModuleNotFoundError: No module named 'backend'`
**Fix**: Updated `backend/main.py` to use correct import paths in Docker container
- Removed 'backend.' prefix from imports when running in container
- Added fallback imports for development compatibility
- Added `/api/health` endpoint for proper load balancer health checks

### 2. Frontend Container Runtime Error  
**Problem**: `sh: next: not found` - Next.js binary missing in runtime
**Fix**: Updated `frontend/Dockerfile` to properly handle dependencies
- Fixed node_modules copying to runtime container
- Used `npm ci` for reliable dependency installation
- Added proper file permissions for nextjs user
- Improved error handling for build process

### 3. Load Balancer Routing Configuration
**Problem**: No API routing rules, both services pointing to wrong target groups
**Fix**: 
- ✅ Fixed ECS services to point to correct target groups
- ✅ Updated frontend target group health check path to `/`
- ✅ Added script to create `/api/*` routing rule to backend

## Deployment Instructions

### Step 1: Pull Latest Code
```bash
cd "C:\AI\GIT_Repos\pdf-to-excel-saas-clean"
git pull origin feat/infrastructure-clean
```

### Step 2: Configure Load Balancer (Run Once)
```bash
python scripts/configure-load-balancer.py
```

### Step 3: Rebuild and Deploy Containers
```bash
# Login to ECR
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com

# Build and push backend
cd backend
docker build -t pdf-excel-saas-backend .
docker tag pdf-excel-saas-backend:latest 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com/pdf-excel-saas-backend:latest
docker push 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com/pdf-excel-saas-backend:latest

# Build and push frontend  
cd ../frontend
docker build -t pdf-excel-saas-frontend .
docker tag pdf-excel-saas-frontend:latest 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com/pdf-excel-saas-frontend:latest
docker push 654499586766.dkr.ecr.ap-southeast-2.amazonaws.com/pdf-excel-saas-frontend:latest
```

### Step 4: Force ECS Service Updates
```bash
# Update backend service
aws ecs update-service --cluster pdf-excel-saas-prod --service pdf-excel-saas-prod-backend-service-ybmcywzr --force-new-deployment --region ap-southeast-2

# Update frontend service
aws ecs update-service --cluster pdf-excel-saas-prod --service pdf-excel-saas-prod-frontend-service-sc418wqq --force-new-deployment --region ap-southeast-2
```

### Step 5: Test Deployment
```bash
# Run comprehensive tests
python scripts/test-deployment.py

# Or wait for services to start first
python scripts/test-deployment.py --wait
```

## Expected Results

After successful deployment:
- ✅ Frontend accessible at: http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com
- ✅ Backend API accessible at: http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com/api/health
- ✅ ECS services running with healthy targets
- ✅ Load balancer routing working correctly

## Troubleshooting

### If containers still fail to start:
1. Check ECS service events:
   ```bash
   aws ecs describe-services --cluster pdf-excel-saas-prod --services pdf-excel-saas-prod-backend-service-ybmcywzr --region ap-southeast-2
   ```

2. Check container logs:
   ```bash
   # Get log streams
   aws logs describe-log-streams --log-group-name "/ecs/pdf-excel-saas-prod-backend" --region ap-southeast-2 --order-by LastEventTime --descending --max-items 1
   
   # Get actual logs  
   aws logs get-log-events --log-group-name "/ecs/pdf-excel-saas-prod-backend" --log-stream-name "STREAM_NAME_FROM_ABOVE" --region ap-southeast-2
   ```

### If 503 errors persist:
1. Wait 5-10 minutes for health checks to pass
2. Verify target group health:
   ```bash
   aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:targetgroup/pdf-excel-saas-prod-frontend-tg1/2d73c25e5780dcbe --region ap-southeast-2
   ```

## Key Configuration Changes Made

### ECS Services:
- Backend service now points to `pdf-excel-saas-prod-backend-tg1`
- Frontend service points to `pdf-excel-saas-prod-frontend-tg1`

### Target Groups:
- Frontend TG health check: `/` (port 3000)
- Backend TG health check: `/api/health` (port 8000)

### Load Balancer Rules:
- Default rule: Forward to frontend target group
- API rule (priority 100): Forward `/api/*` to backend target group

### Container Fixes:
- Backend: Fixed Python import paths for Docker environment
- Frontend: Fixed Next.js build and runtime dependency issues

## Monitoring Commands

```bash
# Check service status
aws ecs describe-services --cluster pdf-excel-saas-prod --services pdf-excel-saas-prod-backend-service-ybmcywzr pdf-excel-saas-prod-frontend-service-sc418wqq --region ap-southeast-2 --query "services[*].[serviceName,status,runningCount,desiredCount]" --output table

# Check target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:targetgroup/pdf-excel-saas-prod-frontend-tg1/2d73c25e5780dcbe --region ap-southeast-2
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:targetgroup/pdf-excel-saas-prod-backend-tg1/624d10cc4f445c11 --region ap-southeast-2

# Test endpoints
curl -I http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com
curl -I http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com/api/health
```

## Notes for Future Development

1. **Environment Variables**: The containers now handle missing environment variables gracefully
2. **Health Checks**: Both services have proper health check endpoints
3. **Import Paths**: Backend code uses relative imports in container, absolute for development
4. **Build Process**: Frontend build is more robust with proper error handling
5. **Load Balancing**: Proper separation of frontend and API traffic

This fix resolves the 503 Service Temporarily Unavailable errors by addressing the root causes:
- Container startup failures
- Missing load balancer routing rules  
- Incorrect target group assignments
