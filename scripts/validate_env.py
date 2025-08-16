#!/usr/bin/env python3
"""
Environment Variable Validation Script
Validates environment variables against schema for different environments
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


class EnvValidator:
    def __init__(self, schema_path: str = "env.schema.json"):
        self.schema_path = schema_path
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict:
        """Load validation schema from JSON file"""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Schema file not found: {self.schema_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in schema file: {e}")
            sys.exit(1)
    
    def _load_env_file(self, env_file: str) -> Dict[str, str]:
        """Load environment variables from .env file"""
        env_vars = {}
        
        if not os.path.exists(env_file):
            print(f"⚠️  Environment file not found: {env_file}")
            return env_vars
            
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '=' not in line:
                    print(f"⚠️  Invalid line format in {env_file}:{line_num}: {line}")
                    continue
                    
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
                
        return env_vars
    
    def _validate_format(self, key: str, value: str) -> List[str]:
        """Validate environment variable format against rules"""
        errors = []
        
        if key not in self.schema.get('validation_rules', {}):
            return errors
            
        rules = self.schema['validation_rules'][key]
        
        # Pattern validation
        if 'pattern' in rules:
            if not re.match(rules['pattern'], value):
                errors.append(f"❌ {key}: Invalid format. {rules.get('description', '')}")
        
        # Minimum length validation
        if 'min_length' in rules:
            if len(value) < rules['min_length']:
                errors.append(f"❌ {key}: Must be at least {rules['min_length']} characters long")
        
        # Check for placeholder values
        placeholder_patterns = [
            r'^your_.*',
            r'^.*_your_.*',
            r'^.*placeholder.*',
            r'^example.*',
            r'^test.*key.*',
            r'^sk_test_.*placeholder.*'
        ]
        
        for pattern in placeholder_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                errors.append(f"⚠️  {key}: Appears to be a placeholder value: {value}")
                break
        
        return errors
    
    def validate_environment(self, environment: str, env_file: Optional[str] = None) -> bool:
        """Validate environment variables for specific environment"""
        
        if environment not in self.schema['environments']:
            print(f"❌ Unknown environment: {environment}")
            return False
        
        env_config = self.schema['environments'][environment]
        required_vars = set(env_config.get('required', []))
        optional_vars = set(env_config.get('optional', []))
        
        # Load environment variables
        if env_file:
            env_vars = self._load_env_file(env_file)
        else:
            env_vars = dict(os.environ)
        
        print(f"\n🔍 Validating {environment} environment...")
        print(f"📁 Source: {'File: ' + env_file if env_file else 'System environment'}")
        print("=" * 60)
        
        errors = []
        warnings = []
        
        # Check required variables
        missing_required = required_vars - set(env_vars.keys())
        if missing_required:
            for var in sorted(missing_required):
                errors.append(f"❌ Missing required variable: {var}")
        
        # Check present variables
        present_vars = set(env_vars.keys())
        known_vars = required_vars | optional_vars
        
        for var in sorted(present_vars & known_vars):
            value = env_vars[var]
            
            # Check for empty values
            if not value or value.strip() == '':
                if var in required_vars:
                    errors.append(f"❌ {var}: Required variable is empty")
                else:
                    warnings.append(f"⚠️  {var}: Optional variable is empty")
                continue
            
            # Format validation
            format_errors = self._validate_format(var, value)
            errors.extend(format_errors)
        
        # Check for unknown variables
        unknown_vars = present_vars - known_vars
        if unknown_vars:
            for var in sorted(unknown_vars):
                warnings.append(f"ℹ️  Unknown variable: {var}")
        
        # Print results
        if errors:
            print("\n🚨 VALIDATION ERRORS:")
            for error in errors:
                print(f"  {error}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  {warning}")
        
        # Summary
        required_present = len(required_vars & present_vars)
        required_total = len(required_vars)
        
        print(f"\n📊 SUMMARY:")
        print(f"  • Required variables: {required_present}/{required_total}")
        print(f"  • Optional variables: {len(optional_vars & present_vars)}/{len(optional_vars)}")
        print(f"  • Unknown variables: {len(unknown_vars)}")
        print(f"  • Errors: {len(errors)}")
        print(f"  • Warnings: {len(warnings)}")
        
        success = len(errors) == 0 and required_present == required_total
        
        if success:
            print(f"\n✅ {environment} environment validation PASSED!")
        else:
            print(f"\n❌ {environment} environment validation FAILED!")
        
        return success
    
    def validate_all_environments(self) -> bool:
        """Validate all available environment files"""
        
        env_files = {
            'local': '.env.local',
            'staging': '.env.staging', 
            'production': '.env.prod'
        }
        
        all_valid = True
        
        for env_name, env_file in env_files.items():
            if os.path.exists(env_file):
                if not self.validate_environment(env_name, env_file):
                    all_valid = False
            else:
                print(f"⚠️  Environment file not found: {env_file}")
        
        return all_valid


def main():
    """Main validation function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate environment variables')
    parser.add_argument('--env', choices=['local', 'staging', 'production'], 
                       help='Environment to validate')
    parser.add_argument('--file', help='Environment file to validate')
    parser.add_argument('--all', action='store_true', 
                       help='Validate all available environment files')
    
    args = parser.parse_args()
    
    validator = EnvValidator()
    
    if args.all:
        success = validator.validate_all_environments()
    elif args.env:
        success = validator.validate_environment(args.env, args.file)
    else:
        print("❌ Please specify --env, --file, or --all")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
