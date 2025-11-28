#!/bin/bash

echo "🔍 CI/CD Setup Verification"
echo "================================"
echo ""

# Check workflow file
if [ -f ".github/workflows/ci-cd.yml" ]; then
    echo "✅ GitHub Actions workflow file exists"
else
    echo "❌ Workflow file missing"
fi

# Check git status
echo ""
echo "📋 Git Status:"
git status --short

# Check AWS credentials (local)
echo ""
echo "🔐 AWS Configuration (local):"
if aws sts get-caller-identity --region us-east-1 &>/dev/null; then
    echo "✅ AWS credentials configured"
    aws sts get-caller-identity --region us-east-1 --query 'Account' --output text
else
    echo "⚠️  AWS credentials not configured locally (not required for CI/CD)"
fi

# Check kubectl access
echo ""
echo "☸️  EKS Access:"
if kubectl get deployment ocrapp-elsondevops &>/dev/null; then
    echo "✅ kubectl can access EKS cluster"
    kubectl get deployment ocrapp-elsondevops -o wide
else
    echo "⚠️  kubectl cannot access EKS (not required for CI/CD)"
fi

# Check ECR repository
echo ""
echo "📦 ECR Repository:"
if aws ecr describe-repositories --repository-names ocrapp-elsondevops --region us-east-1 &>/dev/null; then
    echo "✅ ECR repository exists"
else
    echo "⚠️  Cannot verify ECR repository"
fi

echo ""
echo "================================"
echo "Next Steps:"
echo "1. Add GitHub secrets: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/settings/secrets/actions"
echo "2. Run: ./setup-cicd.sh"
echo "3. Monitor: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions"
