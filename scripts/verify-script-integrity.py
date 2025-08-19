#!/usr/bin/env python3
"""
Script Integrity Verifier - Prevents recurring import issues
Run this after ANY modification to deployment scripts

This tool prevents the recurring issue where critical imports (like 'time')
get lost during script modifications, causing runtime errors like:
"NameError: name 'time' is not defined"

Usage:
    python scripts/verify-script-integrity.py

Add to git pre-commit hook for automatic verification.
"""

import ast
import sys
from pathlib import Path

# Required imports for each script to function properly
REQUIRED_IMPORTS = {
    'destroy-infrastructure.py': [
        'subprocess', 'json', 'sys', 'time', 'Path'
    ],
    'deploy-infrastructure.py': [
        'subprocess', 'json', 'sys', 'time', 'boto3', 'Path', 
        'Dict', 'List', 'dataclass'
    ],
    'validate_env.py': [
        'subprocess', 'json', 'sys', 'Path'
    ],
    'generate-env-vars.py': [
        'subprocess', 'json', 'sys', 'Path'
    ],
    'diagnose-infrastructure.py': [
        'subprocess', 'json', 'sys', 'Path'
    ]
}

# Functions that require specific imports (helps identify usage)
FUNCTION_IMPORT_DEPENDENCIES = {
    'time.time()': 'time',
    'int(time.time())': 'time', 
    'time.sleep()': 'time',
    'boto3.Session()': 'boto3',
    'boto3.client()': 'boto3',
    'session.client()': 'boto3',
    'Path(': 'Path',
    'subprocess.run(': 'subprocess',
    'json.loads(': 'json',
    'json.dumps(': 'json'
}

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_success(msg): 
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_warning(msg): 
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_error(msg): 
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg): 
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def extract_imports_from_ast(script_path):
    """Extract all imports from a Python script using AST"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    # For "from pathlib import Path", add "Path" not "pathlib.Path"
                    imports.add(alias.name)
        
        return imports, content
    except Exception as e:
        return None, f"Error parsing {script_path}: {e}"

def check_function_usage(content, script_name):
    """Check if functions are used without proper imports"""
    issues = []
    
    for func_usage, required_import in FUNCTION_IMPORT_DEPENDENCIES.items():
        if func_usage in content:
            # Check if the required import exists in content
            # Handle both "import time" and "from X import time" patterns
            import_patterns = [
                f"import {required_import}",
                f"from pathlib import {required_import}",  # Special case for Path
                f"from typing import {required_import}",   # Special case for typing
                f"from dataclasses import {required_import}"  # Special case for dataclasses
            ]
            
            found = any(pattern in content for pattern in import_patterns)
            
            if not found:
                issues.append(f"Uses {func_usage} but missing import: {required_import}")
    
    return issues

def verify_script_integrity(script_path, script_name):
    """Verify a single script has all required imports"""
    if not script_path.exists():
        return [f"Script not found: {script_name}"]
    
    imports, content = extract_imports_from_ast(script_path)
    
    if imports is None:  # Error occurred
        return [content]  # content contains error message
    
    errors = []
    required = REQUIRED_IMPORTS.get(script_name, [])
    
    # Check for missing required imports
    missing_imports = []
    for req in required:
        if req not in imports:
            missing_imports.append(req)
    
    if missing_imports:
        errors.append(f"Missing required imports: {missing_imports}")
    
    # Check for function usage without imports
    usage_issues = check_function_usage(content, script_name)
    errors.extend(usage_issues)
    
    return errors

def generate_fix_suggestions(script_name, errors):
    """Generate specific fix suggestions for common issues"""
    suggestions = []
    
    for error in errors:
        if 'time' in error.lower():
            suggestions.append(f"Add 'import time' to the top of {script_name}")
        elif 'boto3' in error.lower():
            suggestions.append(f"Add 'import boto3' to {script_name} and run 'pip install boto3'")
        elif 'path' in error.lower():
            suggestions.append(f"Add 'from pathlib import Path' to {script_name}")
        elif 'subprocess' in error.lower():
            suggestions.append(f"Add 'import subprocess' to {script_name}")
        elif 'json' in error.lower():
            suggestions.append(f"Add 'import json' to {script_name}")
    
    return suggestions

def main():
    """Main verification function"""
    print(f"{Colors.CYAN}=== Script Integrity Verification ==={Colors.END}")
    print("Checking for recurring import issues that cause runtime errors...")
    
    scripts_dir = Path('scripts')
    if not scripts_dir.exists():
        print_error("Scripts directory not found!")
        sys.exit(1)
    
    total_errors = 0
    all_suggestions = []
    
    for script_name in REQUIRED_IMPORTS.keys():
        script_path = scripts_dir / script_name
        print(f"\nChecking {script_name}...")
        
        errors = verify_script_integrity(script_path, script_name)
        
        if errors:
            total_errors += len(errors)
            print_error(f"{script_name} has {len(errors)} issue(s):")
            for error in errors:
                print(f"  • {error}")
            
            # Generate fix suggestions
            suggestions = generate_fix_suggestions(script_name, errors)
            all_suggestions.extend(suggestions)
        else:
            print_success(f"{script_name} - All imports verified")
    
    # Summary
    print(f"\n{Colors.CYAN}=== Verification Summary ==={Colors.END}")
    
    if total_errors == 0:
        print_success("All scripts pass integrity checks!")
        print_info("No import issues detected.")
        return True
    else:
        print_error(f"Found {total_errors} issues across {len(REQUIRED_IMPORTS)} scripts")
        
        if all_suggestions:
            print(f"\n{Colors.YELLOW}🔧 Fix Suggestions:{Colors.END}")
            for suggestion in set(all_suggestions):  # Remove duplicates
                print(f"  • {suggestion}")
        
        print(f"\n{Colors.YELLOW}📚 Common Fixes:{Colors.END}")
        print("  • destroy-infrastructure.py: Add 'import time' at the top")
        print("  • deploy-infrastructure.py: Add 'import boto3' and run 'pip install boto3'")
        print("  • All scripts: Ensure basic imports (subprocess, json, sys, pathlib)")
        
        return False

def create_pre_commit_hook():
    """Create a git pre-commit hook to run this verification automatically"""
    hook_path = Path('.git/hooks/pre-commit')
    
    if hook_path.exists():
        print_info("Pre-commit hook already exists")
        return
    
    hook_content = """#!/bin/bash
# Git pre-commit hook to verify script integrity
cd "$(git rev-parse --show-toplevel)"
python scripts/verify-script-integrity.py
if [ $? -ne 0 ]; then
    echo "❌ Script integrity check failed. Fix imports before committing."
    exit 1
fi
"""
    
    try:
        hook_path.parent.mkdir(exist_ok=True)
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)
        print_success("Created git pre-commit hook for automatic verification")
    except Exception as e:
        print_warning(f"Could not create pre-commit hook: {e}")

if __name__ == "__main__":
    success = main()
    
    if success:
        # Offer to create pre-commit hook
        if not Path('.git/hooks/pre-commit').exists():
            create_hook = input(f"\n{Colors.CYAN}Create git pre-commit hook for automatic verification? (y/N): {Colors.END}")
            if create_hook.lower() == 'y':
                create_pre_commit_hook()
    
    sys.exit(0 if success else 1)
