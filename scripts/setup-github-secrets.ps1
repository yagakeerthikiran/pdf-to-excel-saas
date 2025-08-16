# GitHub Secrets Setup Script for Windows
# This PowerShell script helps you set up all required GitHub repository secrets for CI/CD

param(
    [string]$RepoOwner = "yagakeerthikiran",
    [string]$RepoName = "pdf-to-excel-saas"
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow" 
$InfoColor = "Cyan"

Write-Host "🔐 GitHub Secrets Setup for PDF to Excel SaaS" -ForegroundColor $InfoColor
Write-Host "=============================================" -ForegroundColor $InfoColor

function Write-Status {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $SuccessColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $WarningColor
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $ErrorColor
}

# Check if GitHub CLI is installed
try {
    $ghVersion = gh --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "GitHub CLI found: $($ghVersion[0])"
    } else {
        throw "GitHub CLI not found"
    }
} catch {
    Write-Error "GitHub CLI (gh) not found. Please install it first:"
    Write-Host "https://cli.github.com/" -ForegroundColor $InfoColor
    exit 1
}

# Check if user is authenticated
try {
    gh auth status 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "GitHub CLI authenticated"
    } else {
        throw "Not authenticated"
    }
} catch {
    Write-Error "Please authenticate with GitHub CLI first:"
    Write-Host "gh auth login" -ForegroundColor $InfoColor
    exit 1
}

# Load environment variables from .env.prod
if (-not (Test-Path ".env.prod")) {
    Write-Error ".env.prod file not found. Please create it first using:"
    Write-Host "Copy-Item .env.prod.template .env.prod" -ForegroundColor $InfoColor
    Write-Host "Then edit .env.prod with your actual values." -ForegroundColor $InfoColor
    exit 1
}

Write-Host "`n📝 Loading environment variables from .env.prod..." -ForegroundColor $InfoColor

# Read .env.prod file and create hashtable
$envVars = @{}
Get-Content ".env.prod" | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $envVars[$matches[1].Trim()] = $matches[2].Trim()
    }
}

$repoFullName = "$RepoOwner/$RepoName"
Write-Host "Repository: $repoFullName"

# Function to set secret
function Set-GitHubSecret {
    param(
        [string]$SecretName,
        [string]$SecretValue,
        [string]$Description
    )
    
    if ([string]::IsNullOrEmpty($SecretValue) -or $SecretValue -like "your_*" -or $SecretValue -eq "****") {
        Write-Warning "Skipping $SecretName (empty or placeholder value)"
        return
    }
    
    Write-Host "Setting $SecretName..."
    try {
        gh secret set $SecretName --body $SecretValue --repo $repoFullName 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "$SecretName set successfully"
        } else {
            Write-Error "Failed to set $SecretName"
        }
    } catch {
        Write-Error "Failed to set $SecretName : $_"
    }
}

Write-Host "`n🔑 Setting AWS Secrets..." -ForegroundColor $InfoColor
Set-GitHubSecret "AWS_ACCESS_KEY_ID" $envVars["AWS_ACCESS_KEY_ID"] "AWS Access Key ID"
Set-GitHubSecret "AWS_SECRET_ACCESS_KEY" $envVars["AWS_SECRET_ACCESS_KEY"] "AWS Secret Access Key"
Set-GitHubSecret "AWS_S3_BUCKET_NAME" $envVars["AWS_S3_BUCKET_NAME"] "S3 Bucket Name"

# Get AWS Account ID
try {
    $awsIdentity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -eq 0) {
        $awsAccountId = $awsIdentity.Account
        Set-GitHubSecret "AWS_ACCOUNT_ID" $awsAccountId "AWS Account ID"
        Write-Status "AWS Account ID detected: $awsAccountId"
    } else {
        Write-Warning "AWS CLI not configured. Please set AWS_ACCOUNT_ID secret manually."
    }
} catch {
    Write-Warning "Could not get AWS Account ID. Please set AWS_ACCOUNT_ID secret manually."
}

Write-Host "`n🗄️  Setting Database Secrets..." -ForegroundColor $InfoColor
Set-GitHubSecret "DATABASE_URL" $envVars["DATABASE_URL"] "Database Connection URL"

Write-Host "`n🌐 Setting Application URLs..." -ForegroundColor $InfoColor
Set-GitHubSecret "NEXT_PUBLIC_APP_URL" $envVars["NEXT_PUBLIC_APP_URL"] "Public App URL"
Set-GitHubSecret "BACKEND_URL" $envVars["BACKEND_URL"] "Backend API URL"
Set-GitHubSecret "BACKEND_API_KEY" $envVars["BACKEND_API_KEY"] "Backend API Key"

Write-Host "`n🔐 Setting Supabase Secrets..." -ForegroundColor $InfoColor
Set-GitHubSecret "SUPABASE_URL" $envVars["SUPABASE_URL"] "Supabase Project URL"
Set-GitHubSecret "SUPABASE_SERVICE_ROLE_KEY" $envVars["SUPABASE_SERVICE_ROLE_KEY"] "Supabase Service Role Key"
Set-GitHubSecret "NEXT_PUBLIC_SUPABASE_URL" $envVars["NEXT_PUBLIC_SUPABASE_URL"] "Public Supabase URL"
Set-GitHubSecret "NEXT_PUBLIC_SUPABASE_ANON_KEY" $envVars["NEXT_PUBLIC_SUPABASE_ANON_KEY"] "Public Supabase Anon Key"

Write-Host "`n💳 Setting Stripe Secrets..." -ForegroundColor $InfoColor
Set-GitHubSecret "STRIPE_SECRET_KEY" $envVars["STRIPE_SECRET_KEY"] "Stripe Secret Key"
Set-GitHubSecret "STRIPE_WEBHOOK_SECRET" $envVars["STRIPE_WEBHOOK_SECRET"] "Stripe Webhook Secret"
Set-GitHubSecret "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY" $envVars["NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"] "Public Stripe Key"
Set-GitHubSecret "NEXT_PUBLIC_STRIPE_PRO_PRICE_ID" $envVars["NEXT_PUBLIC_STRIPE_PRO_PRICE_ID"] "Stripe Pro Price ID"

Write-Host "`n🐛 Setting Sentry Secrets..." -ForegroundColor $InfoColor
Set-GitHubSecret "NEXT_PUBLIC_SENTRY_DSN" $envVars["NEXT_PUBLIC_SENTRY_DSN"] "Public Sentry DSN"
Set-GitHubSecret "SENTRY_ORG" $envVars["SENTRY_ORG"] "Sentry Organization"
Set-GitHubSecret "SENTRY_PROJECT" $envVars["SENTRY_PROJECT"] "Sentry Project"
Set-GitHubSecret "SENTRY_AUTH_TOKEN" $envVars["SENTRY_AUTH_TOKEN"] "Sentry Auth Token"

Write-Host "`n📊 Setting PostHog Secrets..." -ForegroundColor $InfoColor
Set-GitHubSecret "NEXT_PUBLIC_POSTHOG_KEY" $envVars["NEXT_PUBLIC_POSTHOG_KEY"] "Public PostHog Key"
Set-GitHubSecret "NEXT_PUBLIC_POSTHOG_HOST" $envVars["NEXT_PUBLIC_POSTHOG_HOST"] "Public PostHog Host"
Set-GitHubSecret "POSTHOG_PROJECT_API_KEY" $envVars["POSTHOG_PROJECT_API_KEY"] "PostHog Project API Key"

Write-Host "`n🔔 Setting Monitoring Secrets..." -ForegroundColor $InfoColor
Set-GitHubSecret "SLACK_WEBHOOK_URL" $envVars["SLACK_WEBHOOK_URL"] "Slack Webhook URL"

# Generate automation GitHub token prompt
if ([string]::IsNullOrEmpty($envVars["GITHUB_TOKEN"]) -or $envVars["GITHUB_TOKEN"] -like "github_pat_*") {
    Write-Host "`n⚠️  AUTOMATION_GITHUB_TOKEN not found." -ForegroundColor $WarningColor
    Write-Host "The monitoring agent needs a GitHub token to create PRs for auto-fixes."
    Write-Host ""
    Write-Host "To create one:"
    Write-Host "1. Go to: https://github.com/settings/tokens?type=beta"
    Write-Host "2. Click 'Generate new token'"
    Write-Host "3. Select repository access: $repoFullName"
    Write-Host "4. Grant permissions: Contents (write), Pull requests (write), Issues (write)"
    Write-Host "5. Copy the token and enter it below"
    Write-Host ""
    $githubToken = Read-Host "Enter your GitHub token (or press Enter to skip)"
    if (-not [string]::IsNullOrEmpty($githubToken)) {
        Set-GitHubSecret "AUTOMATION_GITHUB_TOKEN" $githubToken "Automation GitHub Token"
    }
} else {
    Set-GitHubSecret "AUTOMATION_GITHUB_TOKEN" $envVars["GITHUB_TOKEN"] "Automation GitHub Token"
}

Write-Host "`n🔒 Setting Security Secrets..." -ForegroundColor $InfoColor
# Generate JWT secret if not provided
$jwtSecret = $envVars["JWT_SECRET_KEY"]
if ([string]::IsNullOrEmpty($jwtSecret) -or $jwtSecret.Length -lt 32) {
    Write-Warning "Generating secure JWT secret..."
    $jwtSecret = -join ((1..32) | ForEach-Object { '{0:X}' -f (Get-Random -Maximum 16) })
}
Set-GitHubSecret "JWT_SECRET_KEY" $jwtSecret "JWT Secret Key"

# Generate encryption key if not provided  
$encryptionKey = $envVars["ENCRYPTION_KEY"]
if ([string]::IsNullOrEmpty($encryptionKey) -or $encryptionKey.Length -lt 32) {
    Write-Warning "Generating secure encryption key..."
    $encryptionKey = -join ((1..32) | ForEach-Object { '{0:X}' -f (Get-Random -Maximum 16) })
}
Set-GitHubSecret "ENCRYPTION_KEY" $encryptionKey "Encryption Key"

# List all secrets to verify
Write-Host "`n📋 Verifying GitHub Secrets..." -ForegroundColor $InfoColor
Write-Host "Current repository secrets:"
try {
    gh secret list --repo $repoFullName | Select-Object -First 20
} catch {
    Write-Warning "Could not list secrets. Please verify manually in GitHub."
}

# Check for missing critical secrets
Write-Host "`n🔍 Checking for Missing Critical Secrets..." -ForegroundColor $InfoColor

$criticalSecrets = @(
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY", 
    "AWS_ACCOUNT_ID",
    "DATABASE_URL",
    "STRIPE_SECRET_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "JWT_SECRET_KEY",
    "ENCRYPTION_KEY"
)

$missingSecrets = @()
try {
    $existingSecrets = gh secret list --repo $repoFullName 2>$null
    foreach ($secret in $criticalSecrets) {
        if ($existingSecrets -notmatch "^$secret") {
            $missingSecrets += $secret
        }
    }
} catch {
    Write-Warning "Could not verify secret status."
}

if ($missingSecrets.Count -eq 0) {
    Write-Status "All critical secrets are configured!"
} else {
    Write-Warning "Missing critical secrets:"
    foreach ($secret in $missingSecrets) {
        Write-Host "  - $secret"
    }
    Write-Host ""
    Write-Host "Please set these secrets manually using:"
    Write-Host "gh secret set SECRET_NAME --body 'SECRET_VALUE' --repo $repoFullName" -ForegroundColor $InfoColor
}

# Create secrets documentation
$secretsGuide = @"
# GitHub Secrets Configuration Guide

## Critical Secrets (Required for deployment)
- ``AWS_ACCESS_KEY_ID`` - AWS access key for infrastructure
- ``AWS_SECRET_ACCESS_KEY`` - AWS secret key for infrastructure  
- ``AWS_ACCOUNT_ID`` - Your AWS account ID
- ``DATABASE_URL`` - PostgreSQL connection string
- ``STRIPE_SECRET_KEY`` - Stripe secret key for payments
- ``SUPABASE_SERVICE_ROLE_KEY`` - Supabase service role key
- ``JWT_SECRET_KEY`` - JWT signing secret (32+ chars)
- ``ENCRYPTION_KEY`` - Data encryption key (32+ chars)

## Optional Secrets (For full functionality)
- ``SLACK_WEBHOOK_URL`` - Slack notifications
- ``AUTOMATION_GITHUB_TOKEN`` - Auto-fix PR creation
- ``SENTRY_AUTH_TOKEN`` - Error tracking integration
- ``POSTHOG_PROJECT_API_KEY`` - Analytics integration

## Public Environment Variables (Safe to expose)
- ``NEXT_PUBLIC_SUPABASE_URL``
- ``NEXT_PUBLIC_SUPABASE_ANON_KEY``
- ``NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY``
- ``NEXT_PUBLIC_SENTRY_DSN``
- ``NEXT_PUBLIC_POSTHOG_KEY``
- ``NEXT_PUBLIC_POSTHOG_HOST``

## Setting Secrets (PowerShell)
``````powershell
gh secret set SECRET_NAME --body 'SECRET_VALUE' --repo $repoFullName
``````

## Verification
``````powershell
gh secret list --repo $repoFullName
``````

Generated on: $(Get-Date)
"@

$secretsGuide | Out-File -FilePath "github-secrets-guide.md" -Encoding UTF8
Write-Status "GitHub secrets guide created: github-secrets-guide.md"

Write-Host "`n🎉 GitHub Secrets Setup Complete!" -ForegroundColor $SuccessColor
Write-Host "=================================" -ForegroundColor $SuccessColor
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Verify all secrets are set correctly"
Write-Host "2. Test the deployment pipeline: git push origin main"
Write-Host "3. Monitor the GitHub Actions workflow"
Write-Host "4. Check application deployment at your ALB endpoint"
Write-Host ""
Write-Host "For troubleshooting, check:"
Write-Host "- GitHub Actions logs: https://github.com/$repoFullName/actions"
Write-Host "- AWS CloudWatch logs for ECS services"
Write-Host "- Sentry for application errors"