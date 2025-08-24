# 🚀 PDF to Excel SaaS - CORRECTED DEPLOYMENT COMMANDS

## ⚠️ CORRECTED STEP 2 DEPLOYMENT COMMANDS

### Step 1: Environment Configuration (5 minutes)
1. Copy the environment template:
```bash
cp .env.prod.template .env.prod
```

2. Fill in your actual values in `.env.prod`

### Step 2: Validate Environment & Integrations (10 minutes)
**CORRECTED COMMANDS:**

```bash
# 1. Validate environment variables format
python scripts/validate_env.py --env production

# 2. Test all third-party service integrations  
python scripts/test-integrations.py --file .env.prod
```

### Step 3: Deploy Infrastructure (10 minutes)
```bash
python scripts/deploy-infrastructure.py
```

### Step 4: Deploy Application (15 minutes)
```bash
python scripts/deploy-application.py
```

---

## 🔧 WHAT EACH SCRIPT DOES

### `scripts/validate_env.py --env production`
- ✅ Validates environment variable **format** and **presence**
- ✅ Checks for missing required variables
- ✅ Identifies placeholder values that need to be replaced
- ✅ Validates patterns (AWS keys, Stripe keys, URLs, etc.)
- ❌ **Does NOT test actual connections** to services

### `scripts/test-integrations.py --file .env.prod` 
- ✅ **Tests ACTUAL connections** to all third-party services
- ✅ **AWS**: Validates credentials and tests `aws sts get-caller-identity`
- ✅ **Supabase**: Tests API endpoints and key formats
- ✅ **Stripe**: Connects to Stripe API and validates account
- ✅ **Database**: Tests PostgreSQL connection (if psql available)
- ✅ **Email/SMTP**: Tests SMTP server connectivity  
- ✅ **Sentry**: Validates DSN and endpoint accessibility
- ✅ **PostHog**: Tests API key and host connectivity

---

## 🎯 INTEGRATION TESTING BREAKDOWN

The `test-integrations.py` script is **segregated by service** for easy troubleshooting:

### 🔧 AWS Testing
- Tests AWS CLI availability
- Validates credentials with `aws sts get-caller-identity`
- Confirms Sydney region (ap-southeast-2) configuration
- **Root Cause Detection**: Pinpoints credential vs CLI vs region issues

### 🔐 Supabase Testing  
- Tests API endpoint reachability
- Validates JWT token formats (service role & anonymous keys)
- Tests project accessibility
- **Root Cause Detection**: Separates URL vs key vs format issues

### 💳 Stripe Testing
- Tests Stripe API connection with real account verification
- Validates all key formats (secret, publishable, webhook, price ID)
- Confirms account access and country settings
- **Root Cause Detection**: Identifies key format vs API access vs account issues

### 🗃️ Database Testing
- Tests PostgreSQL connection (if psql client available)
- Validates URL format and Sydney region
- Attempts actual database connection
- **Root Cause Detection**: Separates URL format vs connectivity vs credentials

### 📧 Email Testing
- Tests SMTP server connectivity on specified port
- Validates email address formats
- Checks host reachability
- **Root Cause Detection**: Network vs credentials vs config issues

### 🐛 Sentry Testing
- Tests DSN format and endpoint reachability
- Validates organization and project configuration
- **Root Cause Detection**: DSN vs config vs connectivity issues

### 📊 PostHog Testing
- Tests API key format and connectivity
- Validates host configuration and reachability
- **Root Cause Detection**: Key vs host vs API access issues

---

## 🚨 ERROR IDENTIFICATION EXAMPLES

When a test fails, you'll see **specific error messages** like:

### AWS Issues:
```
❌ FAIL: AWS CLI Available - AWS CLI not installed or not in PATH
❌ FAIL: Credentials Valid - AWS credentials authentication failed
❌ FAIL: Region Check - Incorrect region: us-east-1 (should be ap-southeast-2)
```

### Stripe Issues:
```
❌ FAIL: Secret Key Format - Secret key should start with sk_live_ or sk_test_
❌ FAIL: API Connection - HTTP 401: Invalid API key provided
❌ FAIL: Publishable Key Format - Publishable key should start with pk_live_ or pk_test_
```

### Supabase Issues:
```
❌ FAIL: URL Accessible - Connection failed: [Errno 11001] getaddrinfo failed
❌ FAIL: Service Key Format - Service role key format invalid (should be JWT)
❌ FAIL: Anon Key Check - NEXT_PUBLIC_SUPABASE_ANON_KEY not found
```

### Database Issues:
```
❌ FAIL: Region Check - Database not in Sydney region
❌ FAIL: Connection Test - Database connection failed: FATAL: password authentication failed
❌ FAIL: URL Format - DATABASE_URL should start with postgresql://
```

---

## 🔧 COMMON ISSUES & FIXES

### Issue: "AWS CLI not installed"
**Root Cause**: AWS CLI not available on system  
**Fix**: Install AWS CLI: `pip install awscli` or download from AWS website

### Issue: "AWS credentials authentication failed"  
**Root Cause**: Invalid AWS Access Key or Secret Key  
**Fix**: Generate new credentials in AWS IAM console and update `.env.prod`

### Issue: "Incorrect region: us-east-1 (should be ap-southeast-2)"
**Root Cause**: Wrong AWS region configured  
**Fix**: Change `AWS_REGION=ap-southeast-2` in `.env.prod`

### Issue: "Secret key should start with sk_live_ or sk_test_"
**Root Cause**: Invalid or placeholder Stripe secret key  
**Fix**: Get real secret key from Stripe dashboard and update `.env.prod`

### Issue: "Supabase API endpoint unreachable"
**Root Cause**: Invalid Supabase URL or network issue  
**Fix**: Verify Supabase project URL in Supabase dashboard

### Issue: "Service role key format invalid (should be JWT)"
**Root Cause**: Invalid or placeholder Supabase service role key  
**Fix**: Get JWT token from Supabase Settings → API → service_role key

### Issue: "Database connection failed: FATAL: password authentication failed"
**Root Cause**: Wrong database credentials or database not created yet  
**Fix**: Database will be created during infrastructure deployment, or update credentials

### Issue: "SMTP connection test failed"
**Root Cause**: Wrong SMTP settings or email service not configured  
**Fix**: Update SMTP settings for your email provider (Gmail, etc.)

---

## 📋 RECOMMENDED TESTING SEQUENCE

### Before Deployment:
```bash
# 1. Check environment format
python scripts/validate_env.py --env production

# 2. Test service integrations  
python scripts/test-integrations.py --file .env.prod

# 3. Only proceed if both pass!
```

### If Integration Tests Fail:
1. **Fix the specific failing service** (AWS, Stripe, Supabase, etc.)
2. **Re-run the integration test** to confirm fix
3. **Repeat until all services pass**
4. **Then proceed with deployment**

---

## 🎯 PRODUCTION-READY CHECKLIST

### ✅ Prerequisites
- [ ] `.env.prod` file created and configured
- [ ] `python scripts/validate_env.py --env production` ✅ PASS
- [ ] `python scripts/test-integrations.py --file .env.prod` ✅ PASS
- [ ] AWS CLI installed and accessible
- [ ] Docker installed and running

### ✅ Deployment Sequence
- [ ] `python scripts/deploy-infrastructure.py` ✅ SUCCESS  
- [ ] `python scripts/deploy-application.py` ✅ SUCCESS
- [ ] Application accessible via Load Balancer URL
- [ ] Health check endpoint working: `/health`

---

## 🚀 WHY THIS APPROACH IS BETTER

### **Segregated Testing** = **Faster Debugging**
Instead of failing during deployment and wondering which service is broken, you'll know **exactly** which integration is failing and **why** before you even start deploying.

### **Service-Specific Error Messages** = **Precise Fixes**
No more guessing if it's an AWS issue, Stripe issue, or Supabase issue. The script tells you exactly which service failed and exactly what's wrong.

### **Real Connection Testing** = **Production Confidence**  
Unlike just checking if environment variables exist, this script actually connects to each service to ensure everything works before deployment.

---

## 🎉 READY FOR GO-LIVE!

Once both validation scripts pass, you can confidently deploy knowing that:
- ✅ All environment variables are properly formatted
- ✅ All third-party services are accessible and working
- ✅ Your credentials are valid and active
- ✅ Your configuration is production-ready

**Deploy with confidence using the corrected commands above!** 🚀

---

*Updated: August 2025*  
*Use these corrected commands for your production deployment*
