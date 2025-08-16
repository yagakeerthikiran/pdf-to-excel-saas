# 🪟 Windows Deployment Guide

## 🚀 **Quick Start for Windows Users**

### **Option 1: Simple Batch File (Recommended for Beginners)**

1. **Double-click the deployment script:**
   ```
   scripts\deploy-windows.bat
   ```

2. **Follow the interactive menu:**
   - Check prerequisites
   - Validate environment
   - Deploy infrastructure  
   - Setup GitHub secrets
   - Deploy application

### **Option 2: PowerShell Scripts (Advanced Users)**

1. **Deploy Infrastructure:**
   ```powershell
   .\scripts\deploy-infrastructure.ps1
   ```

2. **Setup GitHub Secrets:**
   ```powershell
   .\scripts\setup-github-secrets.ps1
   ```

### **Option 3: Manual Command Line**

1. **Validate Environment:**
   ```cmd
   python scripts\validate_env.py --env production --file .env.prod
   ```

2. **Deploy with Terraform:**
   ```cmd
   cd infra
   terraform init
   terraform plan -var="environment=prod"
   terraform apply -var="environment=prod"
   ```

---

## 📋 **Windows Prerequisites**

### **Required Software**
• **Git for Windows** - https://git-scm.com/download/win
• **Python 3.11+** - https://python.org/downloads/windows/
• **AWS CLI** - https://aws.amazon.com/cli/
• **Terraform** - https://terraform.io/downloads
• **GitHub CLI** - https://cli.github.com/

### **Optional (for local builds)**
• **Docker Desktop** - https://docker.com/products/docker-desktop/

### **Quick Install with Chocolatey**
```powershell
# Install Chocolatey first: https://chocolatey.org/install
choco install git python awscli terraform gh docker-desktop -y
```

### **Quick Install with Winget**
```powershell
winget install Git.Git
winget install Python.Python.3.11
winget install Amazon.AWSCLI
winget install Hashicorp.Terraform
winget install GitHub.cli
winget install Docker.DockerDesktop
```

---

## 🔧 **Windows-Specific Setup**

### **1. PowerShell Execution Policy**
```powershell
# Allow script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

### **2. Environment Variables**
```cmd
# Add to PATH if not automatically added:
set PATH=%PATH%;C:\Program Files\Git\bin
set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311
set PATH=%PATH%;C:\Program Files\Amazon\AWSCLIV2
```

### **3. Configure AWS CLI**
```cmd
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Default region: us-east-1
# Default output format: json
```

### **4. Authenticate GitHub CLI**
```cmd
gh auth login
# Follow the prompts to authenticate
```

---

## 📁 **File Paths (Windows)**

### **Environment Configuration:**
```
.env.prod.template  → Copy to .env.prod
scripts\validate_env.py
```

### **Deployment Scripts:**
```
scripts\deploy-windows.bat      ← Start here!
scripts\deploy-infrastructure.ps1
scripts\setup-github-secrets.ps1
```

### **Infrastructure:**
```
infra\main.tf
infra\variables.tf
infra\outputs.tf
```

---

## 🎯 **Step-by-Step Windows Deployment**

### **Step 1: Clone Repository**
```cmd
git clone https://github.com/yagakeerthikiran/pdf-to-excel-saas.git
cd pdf-to-excel-saas
git checkout feat/initial-app-foundation
```

### **Step 2: Setup Environment**
```cmd
# Copy template
copy .env.prod.template .env.prod

# Edit with your values
notepad .env.prod
```

### **Step 3: Run Deployment**
```cmd
# Option A: Interactive menu
scripts\deploy-windows.bat

# Option B: Direct PowerShell
PowerShell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1
PowerShell -ExecutionPolicy Bypass -File scripts\setup-github-secrets.ps1
```

### **Step 4: Deploy Application**
```cmd
git add .
git commit -m "Production deployment"
git push origin feat/initial-app-foundation:main
```

---

## 🛠️ **Windows Troubleshooting**

### **PowerShell Execution Policy Error**
```powershell
# Solution 1: Bypass for single script
PowerShell -ExecutionPolicy Bypass -File scripts\deploy-infrastructure.ps1

# Solution 2: Change policy (as Administrator)
Set-ExecutionPolicy RemoteSigned

# Solution 3: Unblock downloaded scripts
Unblock-File scripts\*.ps1
```

### **Path Issues**
```cmd
# Check if tools are in PATH
where git
where python
where aws
where terraform
where gh

# Manually add to PATH if needed
set PATH=%PATH%;C:\path\to\tool
```

### **Python Module Issues**
```cmd
# Install required modules
pip install requests boto3

# Upgrade pip if needed
python -m pip install --upgrade pip
```

### **Git Issues on Windows**
```cmd
# Configure Git for Windows
git config --global core.autocrlf true
git config --global core.filemode false
```

### **Docker Issues**
```cmd
# Start Docker Desktop manually
# Or check if Docker is running:
docker --version
docker ps
```

### **Terraform Issues**
```cmd
# Check Terraform version
terraform version

# Initialize if needed
cd infra
terraform init

# Check AWS provider
terraform providers
```

---

## 📊 **Windows Performance Tips**

### **Faster Terraform on Windows**
```powershell
# Use terraform.exe directly
$env:PATH += ";C:\terraform"

# Cache Terraform plugins
$env:TF_PLUGIN_CACHE_DIR = "C:\terraform-cache"
New-Item -ItemType Directory -Path $env:TF_PLUGIN_CACHE_DIR -Force
```

### **Faster Docker Builds**
```cmd
# Enable BuildKit for faster builds
set DOCKER_BUILDKIT=1

# Use WSL2 backend in Docker Desktop for better performance
```

### **Faster Git Operations**
```cmd
# Configure Git for better Windows performance
git config --global core.preloadindex true
git config --global core.fscache true
git config --global gc.auto 256
```

---

## 🔍 **Windows-Specific Validation**

### **Check Prerequisites Script**
```cmd
# Run prerequisite check
scripts\deploy-windows.bat
# Choose option 5: Check Prerequisites
```

### **Manual Validation**
```cmd
# Check versions
git --version
python --version
aws --version
terraform version
gh --version
docker --version

# Check authentication
aws sts get-caller-identity
gh auth status
```

### **Environment Validation**
```cmd
# Validate .env.prod file
python scripts\validate_env.py --env production --file .env.prod

# Check for Windows line endings (if using Git Bash)
file .env.prod
```

---

## 🚀 **Windows Deployment Summary**

### **What Works on Windows:**
• ✅ **Infrastructure Deployment** - Terraform via PowerShell
• ✅ **Environment Validation** - Python script validation
• ✅ **GitHub Secrets Setup** - GitHub CLI automation
• ✅ **Docker Builds** - Docker Desktop integration
• ✅ **AWS Integration** - Native AWS CLI support
• ✅ **Interactive Deployment** - Batch file interface

### **Windows-Specific Files:**
• `scripts\deploy-windows.bat` - Interactive deployment menu
• `scripts\deploy-infrastructure.ps1` - PowerShell infrastructure script
• `scripts\setup-github-secrets.ps1` - PowerShell secrets setup
• `scripts\validate_env.py` - Cross-platform validation

### **Expected Deployment Time on Windows:**
• **Prerequisites Setup**: 10-15 minutes
• **Environment Configuration**: 5 minutes
• **Infrastructure Deployment**: 15-20 minutes
• **GitHub Setup**: 5 minutes
• **Application Deployment**: 10-15 minutes
• **Total**: ~45-60 minutes

---

## 🎯 **Windows Success Checklist**

### **Before Starting:**
- [ ] Windows 10/11 with PowerShell 5.1+
- [ ] Administrator privileges for software installation
- [ ] Stable internet connection
- [ ] AWS account with billing enabled
- [ ] GitHub account

### **Prerequisites Installed:**
- [ ] Git for Windows
- [ ] Python 3.11+
- [ ] AWS CLI v2
- [ ] Terraform 1.6+
- [ ] GitHub CLI
- [ ] Docker Desktop (optional)

### **Authentication Configured:**
- [ ] AWS CLI: `aws sts get-caller-identity`
- [ ] GitHub CLI: `gh auth status`
- [ ] Git: `git config --global user.name/email`

### **Environment Ready:**
- [ ] `.env.prod` file created and edited
- [ ] Environment validation passes
- [ ] All required service accounts created

### **Deployment Success:**
- [ ] Terraform infrastructure deployed
- [ ] GitHub secrets configured
- [ ] Application pipeline triggered
- [ ] Health checks passing
- [ ] Monitoring active

---

## 🆘 **Windows Support Resources**

### **Common Windows Issues:**
1. **PowerShell execution policy** - Use bypass flag
2. **Path not found errors** - Check environment variables
3. **Permission denied** - Run as administrator
4. **Docker not starting** - Check Docker Desktop
5. **Git line ending issues** - Configure autocrlf

### **Helpful Commands:**
```cmd
# Check PowerShell version
$PSVersionTable.PSVersion

# Check execution policy
Get-ExecutionPolicy

# Check environment PATH
echo %PATH%

# Check Windows version
ver

# Check installed programs
Get-WmiObject -Class Win32_Product | Select-Object Name, Version
```

### **Getting Help:**
• **GitHub Issues**: https://github.com/yagakeerthikiran/pdf-to-excel-saas/issues
• **AWS Documentation**: https://docs.aws.amazon.com/
• **Terraform Documentation**: https://terraform.io/docs
• **Windows PowerShell Help**: `Get-Help`

---

## 🎉 **Windows Deployment Complete!**

Once your deployment succeeds on Windows, you'll have:

• **Production-ready SaaS** running on AWS
• **Intelligent monitoring** with auto-recovery
• **Scalable infrastructure** with load balancing
• **Complete CI/CD pipeline** via GitHub Actions
• **Business analytics** and error tracking
• **Automated billing** with Stripe integration

**Your application will be accessible at the ALB DNS endpoint provided in the deployment summary!**

---

*This guide is specifically optimized for Windows users. For Linux/macOS users, use the bash scripts (.sh files) instead.*