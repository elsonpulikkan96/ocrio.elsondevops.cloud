# CI/CD Quick Start Guide

## 🎯 What This Does
When you push code to the `main` branch, the pipeline automatically:
1. Builds Docker image
2. Pushes to ECR as `ocrapp-elsondevops:latest`
3. Deploys to EKS cluster `ocrapp-elsondevops-app`
4. Updates https://ocrio.elsondevops.cloud/

## 🚀 Quick Setup (3 Steps)

### Step 1: Configure GitHub Secrets
Go to: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/settings/secrets/actions/new

Add these two secrets:
- **AWS_ACCESS_KEY_ID**: (your AWS access key)
- **AWS_SECRET_ACCESS_KEY**: (your AWS secret key)

### Step 2: Verify Runner (Optional)
Check runner status: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/settings/actions/runners

If runner needs setup, SSH to EC2 and run:
```bash
ssh -i "/Users/elsonpealias/us-east-1elson96.pem" ubuntu@ec2-54-205-104-13.compute-1.amazonaws.com -p1243
# Copy and run setup-runner.sh script
```

### Step 3: Push CI/CD Configuration
From your local machine:
```bash
cd /Users/elsonpealias/awsq/ocrio.elsondevops.cloud
./setup-cicd.sh
```

## 📝 Daily Development Workflow

Make changes → Commit → Push → Auto-deploy:
```bash
cd /Users/elsonpealias/awsq/ocrio.elsondevops.cloud

# Make your code changes
vim app/main.py

# Commit and push
git add .
git commit -m "Add new feature"
git push origin main
```

Watch it deploy: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions

## 🔍 Monitoring

**GitHub Actions**: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions

**Check EKS Pods**:
```bash
kubectl get pods -l app=ocrapp-elsondevops
```

**View Logs**:
```bash
kubectl logs -f deployment/ocrapp-elsondevops
```

**Application**: https://ocrio.elsondevops.cloud/

## 🎮 Manual Trigger
1. Go to: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions
2. Select "CI/CD Pipeline"
3. Click "Run workflow" → "Run workflow"

## 📦 What Gets Built
- **Image**: `739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops:latest`
- **Also tagged with**: Commit SHA for version tracking
- **Deployed to**: EKS cluster `ocrapp-elsondevops-app`
- **Accessible at**: https://ocrio.elsondevops.cloud/

## ⚡ That's It!
Every push to `main` = automatic deployment to production.
