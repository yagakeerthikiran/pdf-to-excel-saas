#!/usr/bin/env python3
"""
EMERGENCY TERRAFORM FIX - Remove Duplicate Files
Fixes the duplicate target group configuration error
"""

import os
import sys
from pathlib import Path

def fix_terraform_duplicates():
    """Remove duplicate Terraform files that are causing errors"""
    
    print("🚨 EMERGENCY TERRAFORM FIX")
    print("=" * 50)
    
    # Files that might cause duplicates
    duplicate_files = [
        "infra/target-groups-fix.tf",
        "infra/target-groups-fix.tf.backup", 
        "infra/main.tf.backup",
        "infra/variables.tf.backup",
        "infra/outputs.tf.backup"
    ]
    
    removed_files = []
    
    for file_path in duplicate_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed_files.append(file_path)
                print(f"✅ Removed duplicate file: {file_path}")
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")
        else:
            print(f"ℹ️  File not found (OK): {file_path}")
    
    # Check for any .tf files that might be duplicates
    infra_path = Path("infra")
    if infra_path.exists():
        tf_files = list(infra_path.glob("*.tf"))
        print(f"\n📋 Current .tf files in infra/:")
        for tf_file in tf_files:
            print(f"  - {tf_file}")
            
        # Look for any files with 'fix' or 'backup' in the name
        suspicious_files = [f for f in tf_files if any(word in f.name.lower() for word in ['fix', 'backup', 'temp', 'old'])]
        
        if suspicious_files:
            print(f"\n⚠️  Suspicious files found:")
            for sf in suspicious_files:
                print(f"  - {sf}")
                response = input(f"Remove {sf}? (y/n): ").strip().lower()
                if response == 'y':
                    try:
                        os.remove(sf)
                        removed_files.append(str(sf))
                        print(f"✅ Removed: {sf}")
                    except Exception as e:
                        print(f"❌ Failed to remove {sf}: {e}")
    
    print(f"\n🎯 SUMMARY:")
    if removed_files:
        print(f"✅ Removed {len(removed_files)} duplicate files:")
        for rf in removed_files:
            print(f"  - {rf}")
        print(f"\n🚀 Try running deployment again:")
        print(f"   python scripts\\deploy-infrastructure.py")
    else:
        print(f"ℹ️  No duplicate files found to remove")
        print(f"\n🔍 The issue might be in your local infra/ directory")
        print(f"   Check for any .tf files with duplicate resource names")
    
    return len(removed_files) > 0

def main():
    """Main execution"""
    try:
        fixed = fix_terraform_duplicates()
        sys.exit(0 if fixed else 1)
    except Exception as e:
        print(f"💥 ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
