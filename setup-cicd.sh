#!/bin/bash

echo "🚀 Setting up CI/CD Pipeline..."

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Add and commit the workflow file
git add .github/workflows/ci-cd.yml CICD_SETUP.md setup-cicd.sh
git commit -m "Add CI/CD pipeline with GitHub Actions"

# Push to main branch
echo "📤 Pushing to GitHub..."
git push origin main

echo "✅ CI/CD setup complete!"
echo ""
echo "Next steps:"
echo "1. Add GitHub secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)"
echo "2. Verify self-hosted runner is active"
echo "3. Monitor workflow at: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions"
echo ""
echo "📖 See CICD_SETUP.md for detailed instructions"
