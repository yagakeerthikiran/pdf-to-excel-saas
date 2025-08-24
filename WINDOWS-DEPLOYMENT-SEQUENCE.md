# 🚀 WINDOWS DEPLOYMENT SEQUENCE

## 📥 **STEP -1: PULL LATEST CHANGES**

```cmd
# Navigate to your project directory
cd C:\AI\GIT_Repos\pdf-to-excel-saas-clean

# Check current status and branch
git status
git branch

# Pull all the new changes
git pull origin feat/infrastructure-clean
```

## 🧹 **STEP -0.5: CLEAN BUILD ARTIFACTS (WINDOWS)**

```cmd
# Clean up local build artifacts that conflict with deployment
git restore frontend/package-lock.json
del "frontend\Dockerfile - Copy" 2>nul
del frontend\next.config.js.backup 2>nul

# Verify files are cleaned
dir scripts\test-integrations.py
dir scripts\install-dependencies.py
```

## 🔧 **STEP 0: INSTALL PYTHON DEPENDENCIES**
```cmd
python scripts\install-dependencies.py
```

## 📝 **STEP 1: CONFIGURE ENVIRONMENT**
```cmd
# Copy template and fill with your actual values
copy .env.prod.template .env.prod

# Edit .env.prod with your real credentials using notepad or VS Code
notepad .env.prod
```

## ✅ **STEP 2: VALIDATE & TEST INTEGRATIONS**
```cmd
# Check environment variable formats
python scripts\validate_env.py --env production

# Test ALL service connections with REAL API calls
python scripts\test-integrations.py --file .env.prod
```

## 🏗️ **STEP 3: DEPLOY INFRASTRUCTURE**
```cmd
python scripts\deploy-infrastructure.py
```

## 📦 **STEP 4: DEPLOY APPLICATION**
```cmd
python scripts\deploy-application.py
```

---

## ⚠️ **WINDOWS-SPECIFIC NOTES**

### **File Path Separators:**
- ✅ Use `\` for Windows paths: `scripts\test-integrations.py`
- ✅ Use `/` for Git operations: `git restore frontend/package-lock.json`

### **Command Differences:**
- ✅ `dir` instead of `ls` to list files
- ✅ `del` instead of `rm` to remove files
- ✅ `copy` instead of `cp` to copy files
- ✅ `2>nul` instead of `2>/dev/null` to suppress errors

### **Build Artifact Cleanup (Windows):**
```cmd
# These files get created during local development and should be cleaned
git restore frontend/package-lock.json     # Restore original
del "frontend\Dockerfile - Copy" 2>nul     # Remove backup
del frontend\*.backup 2>nul                # Remove all backups
```

---

## 🎯 **VERIFICATION (WINDOWS)**

After pulling and cleaning, verify:

```cmd
# Check for new integration testing script
dir scripts\test-integrations.py

# Check for dependency installer  
dir scripts\install-dependencies.py

# Check for documentation
dir COMPLETE-DEPLOYMENT-SEQUENCE.md
dir WINDOWS-DEPLOYMENT-SEQUENCE.md
```

---

## 🛡️ **WINDOWS TROUBLESHOOTING**

### **If Python not found:**
```cmd
# Try these alternatives
python3 scripts\validate_env.py --env production
py scripts\validate_env.py --env production
```

### **If Git commands fail:**
```cmd
# Use Git Bash instead of Command Prompt
# Or PowerShell with Linux-style commands
```

### **If file permissions issues:**
```cmd
# Run Command Prompt as Administrator
# Right-click → "Run as administrator"
```

---

**This guide is specifically for Windows environments like yours!** 🪟
