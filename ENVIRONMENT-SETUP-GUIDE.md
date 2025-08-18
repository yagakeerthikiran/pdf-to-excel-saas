# 📋 Complete Environment Variables Setup Guide

This guide provides **step-by-step instructions** to generate all required environment variables for your PDF to Excel SaaS deployment.

## 🚀 **Quick Start (If you can't find infrastructure-outputs.json)**

### **Step 1: Run the Troubleshooter**
```bash
# Navigate to your project directory
cd C:\AI\GIT_Repos\pdf-to-excel-saas

# Run the environment variable generator
python scripts/generate-env-vars.py
```

This script will:
• Check if you're in the right directory
• Look for existing deployment outputs
• Extract values from Terraform if available
• Generate secure keys automatically
• Create/update your .env.prod file
• Show what still needs manual configuration

---

## 📁 **Active Scripts Overview & Flow**

### **🎯 Core Active Scripts (Sydney Region)**

#### **Main Deployment Flow**
```
python scripts/deploy-infrastructure.py
├── scripts/validate_env.py (validates environment)
├── infra/main.tf (Terraform infrastructure)
├── .env.prod.template (environment template)
└── env.schema.json (validation rules)
```

#### **📋 Script Dependencies & Relationships**

• **`scripts/deploy-infrastructure.py`** - **MAIN SCRIPT**
  - ✅ **Purpose**: Complete infrastructure deployment
  - ✅ **Dependencies**: validate_env.py, infra/main.tf
  - ✅ **Output Files**: infrastructure-outputs.json, infrastructure-outputs.env, deployment-summary.md
  - ✅ **Location**: Project root directory

• **`scripts/validate_env.py`** - **VALIDATION SCRIPT**
  - ✅ **Purpose**: Validates environment variables
  - ✅ **Dependencies**: env.schema.json
  - ✅ **Called by**: deploy-infrastructure.py
  - ✅ **Output**: Console validation results

• **`scripts/generate-env-vars.py`** - **TROUBLESHOOTER**
  - ✅ **Purpose**: Generates missing env vars & troubleshoots
  - ✅ **Dependencies**: .env.prod.template
  - ✅ **Output Files**: .env.prod (updated)
  - ✅ **Location**: Project root directory

• **`backend/email_service.py`** - **EMAIL NOTIFICATIONS**
  - ✅ **Purpose**: Replaces Slack with email notifications
  - ✅ **Dependencies**: SMTP environment variables
  - ✅ **Used by**: monitoring/intelligent_agent.py

### **🔄 Script Execution Flow**
```
1. python scripts/generate-env-vars.py  (troubleshoot & generate)
   ↓
2. python scripts/deploy-infrastructure.py  (main deployment)
   ├── validates environment with validate_env.py
   ├── creates Terraform state bucket
   ├── deploys infrastructure with infra/main.tf
   ├── captures outputs to infrastructure-outputs.json
   └── creates deployment-summary.md
   ↓
3. Output files created in project root:
   • infrastructure-outputs.json
   • infrastructure-outputs.env
   • deployment-summary.md
   • .env.prod (if not exists)
```

### **📁 Output Files Location**
All output files are created in the **project root directory** (`C:\AI\GIT_Repos\pdf-to-excel-saas\`):

• **`infrastructure-outputs.json`** - Complete Terraform outputs in JSON format
• **`infrastructure-outputs.env`** - Environment variables format
• **`deployment-summary.md`** - Deployment summary and next steps
• **`.env.prod`** - Production environment file (created if missing)

---

## 🚨 **Technical Debt Cleanup - Duplicate/Inactive Scripts**

### **🗑️ INACTIVE SCRIPTS (Recommend Cleanup)**

• **`scripts/deploy-infrastructure.ps1`** - **DUPLICATE** (PowerShell version)
  - 🚫 **Status**: INACTIVE - Replaced by Python version
  - 🧹 **Action**: Can be deleted (Python version is more robust)

• **`scripts/deploy-infrastructure.sh`** - **DUPLICATE** (Bash version)
  - 🚫 **Status**: INACTIVE - Replaced by Python version
  - 🧹 **Action**: Can be deleted (Python version is more robust)

• **`scripts/deploy-windows.bat`** - **DUPLICATE** (Batch wrapper)
  - 🚫 **Status**: INACTIVE - Calls PowerShell script
  - 🧹 **Action**: Can be deleted (Python version is direct)

• **`scripts/deploy_manual.py`** - **DUPLICATE** (Manual deployment)
  - 🚫 **Status**: INACTIVE - Superseded by main script
  - 🧹 **Action**: Can be deleted (functionality merged)

• **`scripts/setup-github-secrets.ps1/.sh`** - **SEPARATE FEATURE**
  - ⚠️ **Status**: INACTIVE for now (GitHub secrets setup)
  - 🧹 **Action**: Keep for later GitHub Actions setup

• **`scripts/deploy-infrastructure-fix.py`** - **TEMPORARY FIX**
  - 🚫 **Status**: INACTIVE - Fix merged into main script
  - 🧹 **Action**: Can be deleted (fix applied to main script)

• **`infra/serverless.yml`** - **UNUSED CONFIG**
  - 🚫 **Status**: INACTIVE - Using ECS instead of serverless
  - 🧹 **Action**: Can be deleted (not used in current architecture)

### **✅ ACTIVE SCRIPTS (Keep)**

• **`scripts/deploy-infrastructure.py`** - ✅ MAIN DEPLOYMENT SCRIPT
• **`scripts/validate_env.py`** - ✅ ENVIRONMENT VALIDATION  
• **`scripts/generate-env-vars.py`** - ✅ TROUBLESHOOTER
• **`backend/email_service.py`** - ✅ EMAIL NOTIFICATIONS
• **`infra/main.tf`** - ✅ TERRAFORM INFRASTRUCTURE
• **`.env.prod.template`** - ✅ ENVIRONMENT TEMPLATE
• **`env.schema.json`** - ✅ VALIDATION RULES

---

## 📝 **Manual Steps for Each Environment Variable**

### **1. NEXT_PUBLIC_APP_URL & BACKEND_URL**

**Option A: From Infrastructure Outputs (Recommended)**
```bash
# After successful deployment, check these files:
type infrastructure-outputs.json
type infrastructure-outputs.env
```

**Option B: Manual AWS Console Check**
```bash
# Check load balancer DNS
aws elbv2 describe-load-balancers --region ap-southeast-2
```

**Set These Values:**
```bash
NEXT_PUBLIC_APP_URL=http://your-alb-dns-name
BACKEND_URL=http://your-alb-dns-name/api
```

### **2. BACKEND_API_KEY (Auto-Generated)**
```bash
# The generate-env-vars.py script creates this automatically
# Or generate manually:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### **3. DATABASE_URL (Auto-Generated)**
```bash
# Extracted from Terraform outputs automatically
# Format: postgresql://dbadmin:[PASSWORD]@[RDS_ENDPOINT]:5432/pdfexcel
# Password is auto-generated by Terraform
```

### **4. GITHUB_TOKEN**

**Step-by-Step:**
1. Go to GitHub.com → Click your profile → Settings
2. Scroll down → Developer settings → Personal access tokens → Tokens (classic)
3. Click "Generate new token (classic)"
4. **Set expiration**: No expiration (or 1 year)
5. **Select scopes**:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
   - ✅ `write:packages` (Upload packages to GitHub Package Registry)
6. Click "Generate token"
7. **Copy the token** (starts with `ghp_` or `github_pat_`)

```bash
GITHUB_TOKEN=github_pat_11ABCDEFGH_1234567890abcdefghijklmnopqrstuvwxyz
```

### **5. Email Notifications (Replaces Slack)**

**Gmail App Password Setup:**
1. Go to **https://myaccount.google.com/apppasswords**
2. Enable 2-Factor Authentication (required)
3. Generate app password for "Mail"
4. Use this 16-character password (not your Gmail password)

**Step 3: Update Environment Variables**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yagakeerthikiran@gmail.com
SMTP_PASS=your_gmail_app_password
NOTIFICATION_EMAIL=yagakeerthikiran@gmail.com
```

### **6. Supabase Variables (Free Tier)**

**Setup Steps:**
1. Go to https://supabase.com/
2. Create account → Create new project
3. Choose region: **Asia Pacific (Sydney)** for best performance
4. Wait for project setup (2-3 minutes)
5. Go to Settings → API

**Copy These Values:**
```bash
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **7. Stripe Variables (Free for Testing)**

**Setup Steps:**
1. Go to https://stripe.com/ → Create account
2. Complete business verification (can test without full verification)
3. Go to Dashboard → Developers → API keys

**Copy These Values:**
```bash
STRIPE_SECRET_KEY=sk_test_51ABC...  # Use test key initially
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51ABC...
```

**Create Webhook:**
1. Go to Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-alb-dns/stripe-webhook`
3. Select events: `checkout.session.completed`, `customer.subscription.deleted`
4. Copy webhook secret:

```bash
STRIPE_WEBHOOK_SECRET=whsec_ABC123...
```

**Create Product:**
1. Go to Dashboard → Products → Add product
2. Name: "PDF to Excel Pro"
3. Price: Monthly subscription (e.g., $9.99/month)
4. Copy Price ID:

```bash
NEXT_PUBLIC_STRIPE_PRO_PRICE_ID=price_ABC123...
```

### **8. Sentry Variables (Free Tier)**

**Setup Steps:**
1. Go to https://sentry.io/ → Create account
2. Create new project → Choose **React** for frontend tracking
3. Skip manual setup → Go to Settings

**Copy These Values:**
```bash
NEXT_PUBLIC_SENTRY_DSN=https://abc123@o456789.ingest.sentry.io/789012
SENTRY_ORG=your-organization-name
SENTRY_PROJECT=pdf-to-excel-saas
```

**Create Auth Token:**
1. Go to Settings → Auth Tokens
2. Create token with scope: `project:write`

```bash
SENTRY_AUTH_TOKEN=sntrys_ABC123...
```

### **9. PostHog Variables (Free Tier)**

**Setup Steps:**
1. Go to https://posthog.com/ → Create account
2. Choose **Cloud** (US region is fine for analytics)
3. Go to Project Settings

**Copy These Values:**
```bash
NEXT_PUBLIC_POSTHOG_KEY=phc_ABC123...
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
POSTHOG_PROJECT_API_KEY=phc_ABC123...  # Same as above
```

---

## 🔧 **Terraform Backend Error Fix**

### **✅ Fixed in Latest Script**
The deployment script now automatically handles:
• **Backend configuration changes**
• **State migration** with `-migrate-state`
• **Fallback to reconfigure** if migration fails

**Error Message Fixed:**
```
Error: Backend configuration changed
```

**Resolution Applied:**
The script now tries these in order:
1. `terraform init` (normal)
2. `terraform init -migrate-state` (if backend changed)
3. `terraform init -reconfigure` (if migration fails)

---

## 🔧 **Troubleshooting Missing Files**

### **If infrastructure-outputs.json is Missing:**

**Check Current Working Directory:**
```bash
# Make sure you're in the right place
pwd
ls -la
# Should see: README.md, scripts/, infra/, frontend/, backend/
```

**Check Terraform State:**
```bash
cd infra
terraform show
terraform output
```

**Manual AWS Resource Check:**
```bash
# Check S3 buckets
aws s3 ls --region ap-southeast-2 | grep pdf-excel

# Check RDS
aws rds describe-db-instances --region ap-southeast-2

# Check Load Balancers
aws elbv2 describe-load-balancers --region ap-southeast-2

# Check ECR repositories
aws ecr describe-repositories --region ap-southeast-2
```

### **Re-run Deployment if Needed:**
```bash
# If infrastructure isn't deployed yet
python scripts/deploy-infrastructure.py

# This will create infrastructure-outputs.json in project root
```

---

## ✅ **Verification Steps**

### **1. Validate Environment File:**
```bash
python scripts/validate_env.py --env production --file .env.prod
```

### **2. Test Each Service:**

**AWS Connection:**
```bash
aws sts get-caller-identity --region ap-southeast-2
```

**Supabase Connection:**
```bash
# Test URL in browser - should show Supabase API response
curl https://your-project-id.supabase.co/rest/v1/
```

**Stripe Connection:**
```bash
# In your .env.prod directory, test with Python:
python -c "import stripe; stripe.api_key='your_stripe_secret_key'; print(stripe.Account.retrieve())"
```

---

## 🎯 **Complete .env.prod Example**

After following all steps, your `.env.prod` should look like:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=ap-southeast-2
AWS_S3_BUCKET_NAME=pdf-excel-saas-prod-123456789

# Database (Auto-generated)
DATABASE_URL=postgresql://dbadmin:SecurePassword123@pdf-excel-saas-prod-db.abc123.ap-southeast-2.rds.amazonaws.com:5432/pdfexcel

# Application URLs (From Load Balancer)
NEXT_PUBLIC_APP_URL=http://pdf-excel-saas-prod-alb-123456.ap-southeast-2.elb.amazonaws.com
BACKEND_URL=http://pdf-excel-saas-prod-alb-123456.ap-southeast-2.elb.amazonaws.com/api
BACKEND_API_KEY=abc123def456ghi789jkl012mno345pqr678

# Email Notifications (Replaces Slack)
NOTIFICATION_EMAIL=yagakeerthikiran@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yagakeerthikiran@gmail.com
SMTP_PASS=abcd efgh ijkl mnop

# GitHub Integration
GITHUB_TOKEN=github_pat_11ABCDEFGH_1234567890abcdefghijklmnopqrstuvwxyz

# All other services configured...
```

---

## 🚨 **Security Notes**

• **Never commit .env.prod** - it's in .gitignore
• **Use test keys initially** - switch to live keys after testing
• **Rotate secrets regularly** - especially API keys
• **Enable 2FA** on all service accounts
• **Monitor usage** - check AWS billing dashboard

---

## 📞 **Support**

If you encounter issues:

1. **Run the troubleshooter**: `python scripts/generate-env-vars.py`
2. **Check AWS Console**: https://ap-southeast-2.console.aws.amazon.com/
3. **Verify Terraform state**: `cd infra && terraform show`
4. **Check deployment logs** for error messages
5. **Verify output files**: Check project root for infrastructure-outputs.json

The scripts are designed to be **resume-safe** - you can run them multiple times without issues!