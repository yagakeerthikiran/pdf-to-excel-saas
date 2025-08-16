#!/bin/bash
# Make all scripts executable
chmod +x scripts/*.sh

echo "✅ All scripts are now executable"
echo ""
echo "Available scripts:"
echo "• scripts/deploy-infrastructure.sh  - Deploy AWS infrastructure"
echo "• scripts/setup-github-secrets.sh   - Configure GitHub secrets" 
echo "• scripts/validate_env.py          - Validate environment variables"
echo ""
echo "Usage examples:"
echo "  ./scripts/deploy-infrastructure.sh"
echo "  ./scripts/setup-github-secrets.sh"
echo "  python scripts/validate_env.py --env production --file .env.prod"
