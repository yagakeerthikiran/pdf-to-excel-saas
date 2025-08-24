#!/usr/bin/env python3
"""
Install Required Python Dependencies for Deployment Scripts
"""

import subprocess
import sys

def install_package(package):
    """Install a Python package using pip"""
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    """Install all required packages"""
    print("🔧 Installing required Python packages for deployment scripts...")
    
    required_packages = [
        "boto3",           # AWS SDK
        "requests",        # HTTP requests for API testing
        "typing",          # Type hints (built-in for Python 3.5+)
        "dataclasses",     # Data classes (built-in for Python 3.7+)
        "pathlib",         # Path operations (built-in for Python 3.4+)
    ]
    
    failed_packages = []
    
    for package in required_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
        print("Please install these packages manually:")
        for package in failed_packages:
            print(f"  pip install {package}")
        sys.exit(1)
    else:
        print(f"\n🎉 All required packages installed successfully!")
        print("You can now run the deployment scripts.")

if __name__ == "__main__":
    main()
