# 🚀 Production Deployment Automation Guide

## 📋 Quick Start Checklist

### **Prerequisites** ✅
• AWS Account with appropriate permissions
• Domain name for your application  
• GitHub account with CLI access
• Docker installed locally
• Stripe, Supabase, Sentry, PostHog accounts

### **Required Services Setup** ⚙️
• **Stripe**: Create products and get API keys
• **Supabase**: Create project and configure auth
• **Sentry**: Create project for error tracking
• **PostHog**: Create project for analytics  
• **Slack**: Create webhook for notifications

---

## 🏃‍♂️ **One-Click Production Deployment**

### **Step 1: Clone and Setup** 
```bash
git clone https://github.com/yagakeerthikiran/pdf-to-excel-saas.git
cd pdf-to-excel-saas
git checkout feat/initial-app-foundation
```

### **Step 2: Configure Environment**
```bash
# Copy template and edit with your values
cp .env.prod.template .env.prod
nano .env.prod  # Edit with your actual credentials
```

### **Step 3: Validate Configuration**
```bash
# Install Python dependencies for validation
pip install -r scripts/requirements.txt

# Validate all environment variables
python scripts/validate_env.py --env production --file .env.prod
```

### **Step 4: Deploy Infrastructure** 
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Deploy complete AWS infrastructure
./scripts/deploy-infrastructure.sh
```

### **Step 5: Setup GitHub Secrets**
```bash
# Configure GitHub CLI and set all secrets
gh auth login
./scripts/setup-github-secrets.sh
```

### **Step 6: Deploy Application**
```bash
# Push to main branch to trigger deployment
git add .
git commit -m "Production deployment configuration"
git push origin feat/initial-app-foundation:main
```

---

## 🔧 **Manual Infrastructure Setup**

### **AWS Resources Created**
• **VPC**: Complete network setup with public/private subnets
• **RDS**: PostgreSQL database with encryption
• **S3**: File storage bucket with versioning  
• **ECS**: Container cluster with auto-scaling
• **ALB**: Load balancer with health checks
• **ECR**: Container registries for images
• **CloudWatch**: Logging and monitoring

### **Terraform Commands**
```bash
cd infra/
terraform init
terraform plan -var="environment=prod"
terraform apply -var="environment=prod"
```

### **AWS CLI Alternative**
```bash
# Create S3 bucket
aws s3 mb s3://pdf-excel-saas-prod --region us-east-1

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier pdf-excel-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username dbadmin \
  --master-user-password YourSecurePassword123 \
  --allocated-storage 20

# Create ECS cluster
aws ecs create-cluster --cluster-name pdf-excel-cluster
```

---

## 🔐 **Environment Variables Setup**

### **Critical Production Variables**
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIA****************
AWS_SECRET_ACCESS_KEY=****************************************
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=pdf-excel-saas-prod

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Security
JWT_SECRET_KEY=your_jwt_secret_32_chars_minimum
ENCRYPTION_KEY=your_encryption_key_32_chars
```

### **Service Integration**
```bash
# Stripe Payments
STRIPE_SECRET_KEY=sk_live_****
STRIPE_WEBHOOK_SECRET=whsec_****
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_****

# Supabase Auth
SUPABASE_URL=https://project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG****

# Monitoring
NEXT_PUBLIC_SENTRY_DSN=https://****@sentry.io/****
NEXT_PUBLIC_POSTHOG_KEY=phc_****
SLACK_WEBHOOK_URL=https://hooks.slack.com/****
```

---

## 🚀 **GitHub Actions CI/CD Pipeline**

### **Automated Workflow**
1. **Environment Validation**: Check all required variables
2. **Testing**: Run frontend and backend tests
3. **Security Scanning**: Vulnerability assessment  
4. **Docker Build**: Multi-stage container builds
5. **Infrastructure Deployment**: Terraform automation
6. **Application Deployment**: ECS service updates
7. **Health Checks**: Endpoint validation
8. **Monitoring Setup**: Deploy intelligent agent
9. **Notifications**: Slack alerts

### **Trigger Deployment**
```bash
# Automatic on main branch push
git push origin main

# Manual deployment
gh workflow run deploy.yml -f environment=production
```

### **Monitor Deployment**
```bash
# Check workflow status
gh run list --limit 5

# View logs
gh run view --log
```

---

## 🤖 **Intelligent Monitoring Agent**

### **Auto-Recovery Features**
• **Service Health Monitoring**: Continuous health checks
• **Automatic Restarts**: Failed service recovery
• **Dynamic Scaling**: Load-based worker scaling
• **Error Detection**: AI-powered anomaly detection
• **Hotfix Generation**: Automatic code fixes
• **GitHub Integration**: Auto-PR creation
• **Slack Notifications**: Real-time alerts

### **Agent Configuration**
```bash
# Environment variables for monitoring
AUTO_FIX_ENABLED=true
MONITORING_INTERVAL=60
ERROR_THRESHOLD=10
SLACK_WEBHOOK_URL=your_slack_webhook
GITHUB_TOKEN=your_github_token
```

### **Manual Agent Deployment**
```bash
# Deploy monitoring agent
python monitoring/intelligent_agent.py

# Check agent status
aws ecs describe-services --cluster pdf-excel-cluster --services monitoring-agent
```

---

## 📊 **Cost Optimization**

### **Resource Sizing**
• **Frontend**: 0.25 vCPU, 512 MB RAM
• **Backend**: 0.5 vCPU, 1024 MB RAM  
• **Database**: db.t3.micro (dev), scale as needed
• **Workers**: Auto-scaling based on queue length

### **Cost-Saving Strategies**
• Use Spot instances for background workers
• Enable S3 Intelligent Tiering
• Set up CloudWatch alarms for cost monitoring
• Implement auto-scaling policies

### **Monthly Cost Estimate**
```
ECS Fargate:     ~$50-100
RDS db.t3.micro: ~$15-25
S3 Storage:      ~$5-15
ALB:             ~$20
NAT Gateway:     ~$45
CloudWatch:      ~$5-10
-----------------------
Total:           ~$140-215/month
```

---

## 🔒 **Security Best Practices**

### **Network Security**
• VPC with private subnets for databases
• Security groups with minimal access
• WAF protection on ALB
• VPC Flow Logs enabled

### **Data Security**  
• S3 bucket encryption at rest
• RDS encryption enabled
• SSL/TLS certificates
• Secrets stored in GitHub Secrets

### **Application Security**
• Input validation and sanitization
• Rate limiting implementation  
• CORS configuration
• Regular dependency updates

---

## 🩺 **Health Monitoring & Alerts**

### **Health Check Endpoints**
```bash
# Frontend health
curl http://your-alb-dns/api/health

# Backend health
curl http://your-alb-dns/api/health

# Database connectivity
curl http://your-alb-dns/api/db-health
```

### **CloudWatch Dashboards**
• Application performance metrics
• Error rates and response times
• Resource utilization (CPU, Memory)
• Business metrics (conversions, revenue)

### **Alert Configuration**
• High error rates (>5%)
• Response time > 2 seconds  
• Memory usage > 80%
• Failed conversions > 10%

---

## 🛠️ **Troubleshooting Guide**

### **Common Deployment Issues**

**1. Environment Validation Fails**
```bash
# Check missing variables
python scripts/validate_env.py --env production --file .env.prod

# Verify secret formats
grep -E "^[A-Z_]+=.+" .env.prod
```

**2. Terraform Deployment Fails**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Review Terraform state
terraform show

# Check resource limits
aws service-quotas list-service-quotas --service-code ec2
```

**3. Docker Build Issues**
```bash
# Test local builds
docker build -f frontend/Dockerfile.prod -t test-frontend frontend/
docker build -f backend/Dockerfile.prod -t test-backend backend/

# Check ECR permissions
aws ecr get-login-password --region us-east-1
```

**4. ECS Service Issues**
```bash
# Check service status
aws ecs describe-services --cluster pdf-excel-cluster --services frontend backend

# View service logs
aws logs tail /ecs/pdf-excel-prod-frontend --follow
aws logs tail /ecs/pdf-excel-prod-backend --follow
```

**5. Load Balancer Issues**
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# Test endpoints
curl -I http://your-alb-dns/
curl -I http://your-alb-dns/api/health
```

### **Debug Commands**
```bash
# Check ECS task status
aws ecs list-tasks --cluster pdf-excel-cluster
aws ecs describe-tasks --cluster pdf-excel-cluster --tasks task-id

# Monitor CloudWatch logs
aws logs describe-log-groups
aws logs tail /ecs/pdf-excel-prod-backend --follow

# Check S3 bucket access
aws s3 ls s3://pdf-excel-saas-prod
aws s3api get-bucket-policy --bucket pdf-excel-saas-prod
```

---

## 📈 **Performance Optimization**

### **Database Optimization**
• Connection pooling configuration
• Query optimization and indexing
• Read replicas for scaling
• Regular maintenance windows

### **Application Optimization**  
• Redis caching layer
• CDN for static assets
• Image optimization
• Code splitting and lazy loading

### **Infrastructure Optimization**
• Auto-scaling policies
• Container resource optimization
• Load balancer configuration
• CloudFront CDN setup

---

## 🎯 **Business Metrics Tracking**

### **Key Performance Indicators**
• User registration and conversion rates
• File upload and conversion success rates  
• Subscription upgrade rates
• Customer retention and churn
• Revenue attribution and LTV

### **PostHog Events**
```javascript
// Track key business events
posthog.capture('user_registered')
posthog.capture('file_uploaded', { file_size: size })
posthog.capture('conversion_completed', { processing_time: time })
posthog.capture('subscription_upgraded', { plan: 'pro' })
```

---

## 🔄 **Continuous Deployment**

### **Deployment Strategies**
• **Blue-Green**: Zero-downtime deployments
• **Rolling Updates**: Gradual service updates
• **Canary Releases**: Gradual traffic shifting
• **Feature Flags**: Safe feature rollouts

### **Rollback Procedures**
```bash
# Quick rollback via ECS
aws ecs update-service --cluster pdf-excel-cluster \
  --service frontend --task-definition previous-revision

# Database migration rollback
python manage.py migrate app_name previous_migration

# Infrastructure rollback
terraform apply -target=resource.name previous.tfstate
```

---

## 📞 **Production Support**

### **Monitoring Dashboards**
• **Application**: http://your-alb-dns
• **AWS Console**: https://console.aws.amazon.com/
• **GitHub Actions**: https://github.com/yagakeerthikiran/pdf-to-excel-saas/actions
• **Sentry**: https://sentry.io/organizations/your-org/
• **PostHog**: https://app.posthog.com/

### **Emergency Contacts**
• **AWS Support**: Technical infrastructure issues
• **GitHub Support**: CI/CD pipeline issues  
• **Sentry Alerts**: Application errors
• **Slack Notifications**: Real-time alerts

### **Escalation Procedures**
1. **Level 1**: Automatic monitoring agent response
2. **Level 2**: Slack alerts to development team
3. **Level 3**: Email notifications to technical leads
4. **Level 4**: Manual intervention and AWS support

---

## ✅ **Production Readiness Checklist**

### **Infrastructure** 
- [ ] AWS resources provisioned
- [ ] Domain configured with SSL
- [ ] Database migrations applied
- [ ] S3 bucket policies set
- [ ] Security groups configured
- [ ] Backup procedures tested

### **Application**
- [ ] Environment variables validated
- [ ] Docker images built and pushed
- [ ] ECS services deployed
- [ ] Load balancer health checks passing
- [ ] API endpoints responding
- [ ] File upload/download working

### **Monitoring**
- [ ] Sentry error tracking active
- [ ] PostHog analytics configured  
- [ ] CloudWatch dashboards created
- [ ] Slack notifications working
- [ ] Intelligent agent deployed
- [ ] Health check alerts configured

### **Security**
- [ ] SSL certificates installed
- [ ] WAF protection enabled
- [ ] Security groups reviewed
- [ ] Secrets management configured
- [ ] Access controls verified
- [ ] Vulnerability scan completed

### **Business**
- [ ] Stripe payments tested
- [ ] Subscription flows working
- [ ] Email notifications active
- [ ] Analytics tracking events
- [ ] User onboarding tested
- [ ] Support documentation updated

---

## 🎉 **Deployment Complete!**

Your PDF to Excel SaaS is now production-ready with:

• **Scalable Infrastructure**: Auto-scaling ECS with load balancing
• **Intelligent Monitoring**: Self-healing capabilities
• **Business Analytics**: Revenue and user tracking
• **Security**: Enterprise-grade protection
• **Support**: 24/7 monitoring and alerts

**🌐 Access your application**: http://your-alb-dns  
**📊 Monitor performance**: CloudWatch + Sentry + PostHog  
**🔧 Manage infrastructure**: AWS Console + Terraform  
**🤖 Auto-recovery**: Intelligent monitoring agent active

---

*Generated on: $(date)*  
*Repository: https://github.com/yagakeerthikiran/pdf-to-excel-saas*