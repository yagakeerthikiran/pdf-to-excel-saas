#!/bin/bash
# GitHub Secrets Setup Script
# This script helps you set up all required GitHub repository secrets for CI/CD

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 GitHub Secrets Setup for PDF to Excel SaaS${NC}"
echo -e "${BLUE}=============================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) not found. Please install it first:"
    echo "https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    print_error "Please authenticate with GitHub CLI first:"
    echo "gh auth login"
    exit 1
fi

print_status "GitHub CLI authenticated"

# Load environment variables from .env.prod
if [ ! -f ".env.prod" ]; then
    print_error ".env.prod file not found. Please create it first using:"
    echo "cp .env.prod.template .env.prod"
    echo "Then edit .env.prod with your actual values."
    exit 1
fi

echo -e "\n${BLUE}📝 Loading environment variables from .env.prod...${NC}"
source .env.prod

# Get repository info
REPO_OWNER="yagakeerthikiran"
REPO_NAME="pdf-to-excel-saas"
REPO_FULL_NAME="$REPO_OWNER/$REPO_NAME"

echo "Repository: $REPO_FULL_NAME"

# Function to set secret
set_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    if [ -z "$secret_value" ] || [ "$secret_value" = "your_*" ] || [ "$secret_value" = "****" ]; then
        print_warning "Skipping $secret_name (empty or placeholder value)"
        return
    fi
    
    echo "Setting $secret_name..."
    if gh secret set "$secret_name" --body "$secret_value" --repo "$REPO_FULL_NAME"; then
        print_status "$secret_name set successfully"
    else
        print_error "Failed to set $secret_name"
    fi
}

echo -e "\n${BLUE}🔑 Setting AWS Secrets...${NC}"
set_secret "AWS_ACCESS_KEY_ID" "$AWS_ACCESS_KEY_ID" "AWS Access Key ID"
set_secret "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key"
set_secret "AWS_S3_BUCKET_NAME" "$AWS_S3_BUCKET_NAME" "S3 Bucket Name"

# Get AWS Account ID
if command -v aws &> /dev/null && aws sts get-caller-identity &> /dev/null; then
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    set_secret "AWS_ACCOUNT_ID" "$AWS_ACCOUNT_ID" "AWS Account ID"
    print_status "AWS Account ID detected: $AWS_ACCOUNT_ID"
else
    print_warning "AWS CLI not configured. Please set AWS_ACCOUNT_ID secret manually."
fi

echo -e "\n${BLUE}🗄️  Setting Database Secrets...${NC}"
set_secret "DATABASE_URL" "$DATABASE_URL" "Database Connection URL"

echo -e "\n${BLUE}🌐 Setting Application URLs...${NC}"
set_secret "NEXT_PUBLIC_APP_URL" "$NEXT_PUBLIC_APP_URL" "Public App URL"
set_secret "BACKEND_URL" "$BACKEND_URL" "Backend API URL"
set_secret "BACKEND_API_KEY" "$BACKEND_API_KEY" "Backend API Key"

echo -e "\n${BLUE}🔐 Setting Supabase Secrets...${NC}"
set_secret "SUPABASE_URL" "$SUPABASE_URL" "Supabase Project URL"
set_secret "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_ROLE_KEY" "Supabase Service Role Key"
set_secret "NEXT_PUBLIC_SUPABASE_URL" "$NEXT_PUBLIC_SUPABASE_URL" "Public Supabase URL"
set_secret "NEXT_PUBLIC_SUPABASE_ANON_KEY" "$NEXT_PUBLIC_SUPABASE_ANON_KEY" "Public Supabase Anon Key"

echo -e "\n${BLUE}💳 Setting Stripe Secrets...${NC}"
set_secret "STRIPE_SECRET_KEY" "$STRIPE_SECRET_KEY" "Stripe Secret Key"
set_secret "STRIPE_WEBHOOK_SECRET" "$STRIPE_WEBHOOK_SECRET" "Stripe Webhook Secret"
set_secret "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY" "$NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY" "Public Stripe Key"
set_secret "NEXT_PUBLIC_STRIPE_PRO_PRICE_ID" "$NEXT_PUBLIC_STRIPE_PRO_PRICE_ID" "Stripe Pro Price ID"

echo -e "\n${BLUE}🐛 Setting Sentry Secrets...${NC}"
set_secret "NEXT_PUBLIC_SENTRY_DSN" "$NEXT_PUBLIC_SENTRY_DSN" "Public Sentry DSN"
set_secret "SENTRY_ORG" "$SENTRY_ORG" "Sentry Organization"
set_secret "SENTRY_PROJECT" "$SENTRY_PROJECT" "Sentry Project"
set_secret "SENTRY_AUTH_TOKEN" "$SENTRY_AUTH_TOKEN" "Sentry Auth Token"

echo -e "\n${BLUE}📊 Setting PostHog Secrets...${NC}"
set_secret "NEXT_PUBLIC_POSTHOG_KEY" "$NEXT_PUBLIC_POSTHOG_KEY" "Public PostHog Key"
set_secret "NEXT_PUBLIC_POSTHOG_HOST" "$NEXT_PUBLIC_POSTHOG_HOST" "Public PostHog Host"
set_secret "POSTHOG_PROJECT_API_KEY" "$POSTHOG_PROJECT_API_KEY" "PostHog Project API Key"

echo -e "\n${BLUE}🔔 Setting Monitoring Secrets...${NC}"
set_secret "SLACK_WEBHOOK_URL" "$SLACK_WEBHOOK_URL" "Slack Webhook URL"

# Generate automation GitHub token prompt
if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "github_pat_*" ]; then
    echo -e "\n${YELLOW}⚠️  AUTOMATION_GITHUB_TOKEN not found.${NC}"
    echo "The monitoring agent needs a GitHub token to create PRs for auto-fixes."
    echo ""
    echo "To create one:"
    echo "1. Go to: https://github.com/settings/tokens?type=beta"
    echo "2. Click 'Generate new token'"
    echo "3. Select repository access: $REPO_FULL_NAME"
    echo "4. Grant permissions: Contents (write), Pull requests (write), Issues (write)"
    echo "5. Copy the token and set it as AUTOMATION_GITHUB_TOKEN secret"
    echo ""
    read -p "Enter your GitHub token (or press Enter to skip): " github_token
    if [ ! -z "$github_token" ]; then
        set_secret "AUTOMATION_GITHUB_TOKEN" "$github_token" "Automation GitHub Token"
    fi
else
    set_secret "AUTOMATION_GITHUB_TOKEN" "$GITHUB_TOKEN" "Automation GitHub Token"
fi

echo -e "\n${BLUE}🔒 Setting Security Secrets...${NC}"
# Generate JWT secret if not provided
if [ -z "$JWT_SECRET_KEY" ] || [ ${#JWT_SECRET_KEY} -lt 32 ]; then
    print_warning "Generating secure JWT secret..."
    JWT_SECRET_KEY=$(openssl rand -hex 32)
fi
set_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY" "JWT Secret Key"

# Generate encryption key if not provided
if [ -z "$ENCRYPTION_KEY" ] || [ ${#ENCRYPTION_KEY} -lt 32 ]; then
    print_warning "Generating secure encryption key..."
    ENCRYPTION_KEY=$(openssl rand -hex 32)
fi
set_secret "ENCRYPTION_KEY" "$ENCRYPTION_KEY" "Encryption Key"

# List all secrets to verify
echo -e "\n${BLUE}📋 Verifying GitHub Secrets...${NC}"
echo "Current repository secrets:"
gh secret list --repo "$REPO_FULL_NAME" | head -20

# Check for missing critical secrets
echo -e "\n${BLUE}🔍 Checking for Missing Critical Secrets...${NC}"

CRITICAL_SECRETS=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AWS_ACCOUNT_ID"
    "DATABASE_URL"
    "STRIPE_SECRET_KEY"
    "SUPABASE_SERVICE_ROLE_KEY"
    "JWT_SECRET_KEY"
    "ENCRYPTION_KEY"
)

missing_secrets=()
for secret in "${CRITICAL_SECRETS[@]}"; do
    if ! gh secret list --repo "$REPO_FULL_NAME" | grep -q "^$secret"; then
        missing_secrets+=("$secret")
    fi
done

if [ ${#missing_secrets[@]} -eq 0 ]; then
    print_status "All critical secrets are configured!"
else
    print_warning "Missing critical secrets:"
    for secret in "${missing_secrets[@]}"; do
        echo "  - $secret"
    done
    echo ""
    echo "Please set these secrets manually using:"
    echo "gh secret set SECRET_NAME --body 'SECRET_VALUE' --repo $REPO_FULL_NAME"
fi

# Create secrets documentation
cat > github-secrets-guide.md << EOF
# GitHub Secrets Configuration Guide

## Critical Secrets (Required for deployment)
- \`AWS_ACCESS_KEY_ID\` - AWS access key for infrastructure
- \`AWS_SECRET_ACCESS_KEY\` - AWS secret key for infrastructure  
- \`AWS_ACCOUNT_ID\` - Your AWS account ID
- \`DATABASE_URL\` - PostgreSQL connection string
- \`STRIPE_SECRET_KEY\` - Stripe secret key for payments
- \`SUPABASE_SERVICE_ROLE_KEY\` - Supabase service role key
- \`JWT_SECRET_KEY\` - JWT signing secret (32+ chars)
- \`ENCRYPTION_KEY\` - Data encryption key (32+ chars)

## Optional Secrets (For full functionality)
- \`SLACK_WEBHOOK_URL\` - Slack notifications
- \`AUTOMATION_GITHUB_TOKEN\` - Auto-fix PR creation
- \`SENTRY_AUTH_TOKEN\` - Error tracking integration
- \`POSTHOG_PROJECT_API_KEY\` - Analytics integration

## Public Environment Variables (Safe to expose)
- \`NEXT_PUBLIC_SUPABASE_URL\`
- \`NEXT_PUBLIC_SUPABASE_ANON_KEY\`
- \`NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY\`
- \`NEXT_PUBLIC_SENTRY_DSN\`
- \`NEXT_PUBLIC_POSTHOG_KEY\`
- \`NEXT_PUBLIC_POSTHOG_HOST\`

## Setting Secrets
\`\`\`bash
gh secret set SECRET_NAME --body 'SECRET_VALUE' --repo $REPO_FULL_NAME
\`\`\`

## Verification
\`\`\`bash
gh secret list --repo $REPO_FULL_NAME
\`\`\`

Generated on: $(date)
EOF

print_status "GitHub secrets guide created: github-secrets-guide.md"

echo -e "\n${GREEN}🎉 GitHub Secrets Setup Complete!${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""
echo "Next steps:"
echo "1. Verify all secrets are set correctly"
echo "2. Test the deployment pipeline: git push origin main"
echo "3. Monitor the GitHub Actions workflow"
echo "4. Check application deployment at your ALB endpoint"
echo ""
echo "For troubleshooting, check:"
echo "- GitHub Actions logs: https://github.com/$REPO_FULL_NAME/actions"
echo "- AWS CloudWatch logs for ECS services"
echo "- Sentry for application errors"
