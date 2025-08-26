# Environment Variables Setup Guide

## 🎯 **Complete Solution for .env.prod Template**

This guide shows how to handle all environment variables from `.env.prod.template` using **AWS Parameter Store** - a secure, scalable approach that doesn't require gitignored files.

## 🚀 **Quick Setup (5 minutes)**

### **Step 1: Run Basic Setup**
```bash
# Make script executable
chmod +x scripts/setup-parameter-store.sh

# Run setup (creates basic parameters)
./scripts/setup-parameter-store.sh
```

This creates:
• Basic app URLs and configuration
• Auto-generated JWT and encryption keys  
• Monitoring settings
• Secure parameter structure

### **Step 2: Add Integration Services (As Needed)**

**Only set up the services you actually need:**

#### **🔐 Database (Required for data persistence)**
```bash
# After setting up RDS
aws ssm put-parameter --region ap-southeast-2 \
  --name '/pdf-excel-saas/prod/database/url' \
  --value 'postgresql://dbadmin:YOUR_PASSWORD@YOUR_RDS_ENDPOINT:5432/pdfexcel' \
  --type 'SecureString'
```

#### **👤 Supabase Auth (Optional - for user authentication)**
```bash
# After creating Supabase project
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/supabase/url' --value 'https://YOUR_PROJECT.supabase.co' --type 'String'
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/supabase/service-key' --value 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR_SERVICE_KEY' --type 'SecureString'
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/supabase/anon-key' --value 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR_ANON_KEY' --type 'String'
```

#### **💳 Stripe Payments (Optional - for subscriptions)**
```bash
# After setting up Stripe account
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/stripe/secret-key' --value 'sk_live_YOUR_SECRET_KEY' --type 'SecureString'
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/stripe/publishable-key' --value 'pk_live_YOUR_PUBLISHABLE_KEY' --type 'String'
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/stripe/webhook-secret' --value 'whsec_YOUR_WEBHOOK_SECRET' --type 'SecureString'
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/stripe/pro-price-id' --value 'price_YOUR_PRICE_ID' --type 'String'
```

#### **📧 Email (Optional - for notifications)**
```bash
# Using Gmail as example
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/email/smtp-user' --value 'your-email@gmail.com' --type 'String'
aws ssm put-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/email/smtp-password' --value 'your-app-password' --type 'SecureString'
```

## 🔄 **How It Works**

### **During Deployment:**
1. CI/CD fetches parameters from AWS Parameter Store
2. Required parameters get fallback values if missing
3. Optional parameters are only added if they exist
4. Environment variables are injected into ECS containers
5. App works with whatever services are configured

### **Benefits:**
• ✅ **Secure**: Sensitive data encrypted in AWS Parameter Store
• ✅ **Scalable**: No dependency on gitignored files  
• ✅ **Flexible**: Add services incrementally as needed
• ✅ **Automatic**: CI/CD handles everything
• ✅ **Resume-Safe**: Missing services don't break deployment

## 📋 **Current Implementation Status**

### **✅ Working Right Now:**
- Basic frontend/backend communication
- AWS S3 integration for file storage
- JWT authentication
- Health checks and monitoring

### **🔧 Add When Needed:**
- Database (when you need data persistence)
- Supabase (when you need user authentication)  
- Stripe (when you need payments)
- Email (when you need notifications)
- Sentry (when you need error tracking)
- PostHog (when you need analytics)

## 🎯 **Next Steps**

1. **Test Current App**: Buttons should now work with basic functionality
2. **Add Database**: When you need to store user data and conversions
3. **Add Auth**: When you need user accounts (Supabase)
4. **Add Payments**: When you want subscriptions (Stripe)
5. **Add Monitoring**: When you want error tracking (Sentry)

## 📖 **View All Parameters**
```bash
# List all current parameters
aws ssm get-parameters-by-path --region ap-southeast-2 --path '/pdf-excel-saas/prod' --recursive

# Get specific parameter
aws ssm get-parameter --region ap-southeast-2 --name '/pdf-excel-saas/prod/app/frontend-url'
```

The app now works incrementally - you can add services as you need them without breaking existing functionality!