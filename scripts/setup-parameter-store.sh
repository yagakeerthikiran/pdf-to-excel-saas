#!/bin/bash

# PDF to Excel SaaS - AWS Parameter Store Setup
# This script creates all required environment variables in AWS Parameter Store
# Run once to set up, then CI/CD can fetch values automatically

set -e

AWS_REGION="ap-southeast-2"
APP_PREFIX="/pdf-excel-saas/prod"

echo "🔧 Setting up AWS Parameter Store for PDF to Excel SaaS..."
echo "Region: $AWS_REGION"
echo "Prefix: $APP_PREFIX"

# Function to create parameter
create_parameter() {
    local name=$1
    local value=$2
    local type=${3:-"String"}
    local description=$4
    
    echo "Creating parameter: $name"
    aws ssm put-parameter \
        --region $AWS_REGION \
        --name "$APP_PREFIX/$name" \
        --value "$value" \
        --type "$type" \
        --description "$description" \
        --overwrite \
        --tags "Key=Environment,Value=production" "Key=Project,Value=pdf-excel-saas"
}

# AWS Configuration
create_parameter "aws/region" "ap-southeast-2" "String" "AWS Region"
create_parameter "aws/s3-bucket" "pdf-excel-saas-prod" "String" "S3 Bucket Name"

# Application URLs
ALB_URL="http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com"
create_parameter "app/frontend-url" "$ALB_URL" "String" "Frontend Application URL"
create_parameter "app/backend-url" "$ALB_URL/api" "String" "Backend API URL"

# JWT & Security
create_parameter "security/jwt-secret" "$(openssl rand -base64 32)" "SecureString" "JWT Secret Key"
create_parameter "security/encryption-key" "$(openssl rand -base64 32)" "SecureString" "Data Encryption Key"

# Monitoring & Auto-fix
create_parameter "monitoring/auto-fix-enabled" "false" "String" "Enable AI auto-fix"
create_parameter "monitoring/interval" "300" "String" "Monitor interval in seconds"
create_parameter "monitoring/error-threshold" "20" "String" "Error threshold"

echo ""
echo "✅ Basic parameters created successfully!"
echo ""
echo "🔑 MANUAL SETUP REQUIRED:"
echo "You need to manually set these sensitive parameters:"
echo ""
echo "# Database (after RDS setup)"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/database/url' --value 'postgresql://dbadmin:PASSWORD@ENDPOINT/pdfexcel' --type 'SecureString'"
echo ""
echo "# Supabase (after project creation)"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/supabase/url' --value 'https://PROJECT.supabase.co' --type 'String'"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/supabase/service-key' --value 'eyJ...' --type 'SecureString'"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/supabase/anon-key' --value 'eyJ...' --type 'String'"
echo ""
echo "# Stripe (after account setup)"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/stripe/secret-key' --value 'sk_live_...' --type 'SecureString'"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/stripe/publishable-key' --value 'pk_live_...' --type 'String'"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/stripe/webhook-secret' --value 'whsec_...' --type 'SecureString'"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/stripe/pro-price-id' --value 'price_...' --type 'String'"
echo ""
echo "# Email (if using Gmail)"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/email/smtp-user' --value 'your-email@gmail.com' --type 'String'"
echo "aws ssm put-parameter --region $AWS_REGION --name '$APP_PREFIX/email/smtp-password' --value 'app-password' --type 'SecureString'"
echo ""
echo "📋 To list all parameters:"
echo "aws ssm get-parameters-by-path --region $AWS_REGION --path '$APP_PREFIX' --recursive"