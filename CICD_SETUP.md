# CI/CD Setup Guide

## Overview
This CI/CD pipeline automatically builds, pushes to ECR, and deploys to EKS when code is pushed to the `main` branch.

## Prerequisites Completed
- ✅ Self-hosted GitHub Actions runner on EC2 (i-0c348c58aab3a9b30)
- ✅ EKS Cluster: ocrapp-elsondevops-app
- ✅ ECR Repository: ocrapp-elsondevops
- ✅ GitHub Repository: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud

## Setup Steps

### 1. Configure GitHub Secrets
Add these secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### 2. Verify Self-Hosted Runner
Ensure your EC2 runner is active:
- Go to: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/settings/actions/runners
- Status should show "Idle" or "Active"

### 3. Runner Prerequisites on EC2
SSH into your runner and verify:
```bash
ssh -i "/Users/elsonpealias/us-east-1elson96.pem" ubuntu@ec2-54-205-104-13.compute-1.amazonaws.com -p1243

# Check installations
docker --version
aws --version
kubectl version --client
```

If missing, install:
```bash
# Docker
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## Workflow Trigger

### Automatic Trigger
Push to main branch:
```bash
cd /Users/elsonpealias/awsq/ocrio.elsondevops.cloud
git add .
git commit -m "Your commit message"
git push origin main
```

### Manual Trigger
Go to: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions
- Select "CI/CD Pipeline"
- Click "Run workflow"

## Pipeline Stages

1. **Checkout**: Pulls latest code from main branch
2. **Configure AWS**: Sets up AWS credentials
3. **ECR Login**: Authenticates with Amazon ECR
4. **Build**: Creates Docker image from Dockerfile
5. **Push**: Pushes image to ECR with `latest` and commit SHA tags
6. **Deploy**: Restarts EKS deployment to pull new image
7. **Verify**: Confirms deployment success

## Monitoring

### View Workflow Runs
https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions

### Check EKS Deployment
```bash
kubectl get pods -n default -l app=ocrapp-elsondevops
kubectl logs -f deployment/ocrapp-elsondevops -n default
```

### Access Application
https://ocrio.elsondevops.cloud/

## Troubleshooting

### Runner Offline
```bash
# SSH to EC2
ssh -i "/Users/elsonpealias/us-east-1elson96.pem" ubuntu@ec2-54-205-104-13.compute-1.amazonaws.com -p1243

# Check runner service
cd actions-runner
./run.sh
```

### ECR Push Fails
Verify IAM permissions for ECR push on the AWS credentials used.

### EKS Deployment Fails
```bash
kubectl describe deployment ocrapp-elsondevops -n default
kubectl get events -n default --sort-by='.lastTimestamp'
```

## Development Workflow

1. Make code changes in `/Users/elsonpealias/awsq/ocrio.elsondevops.cloud`
2. Test locally if needed
3. Commit and push to main:
   ```bash
   git add .
   git commit -m "Feature: description"
   git push origin main
   ```
4. Monitor workflow: https://github.com/elsonpulikkan96/ocrio.elsondevops.cloud/actions
5. Verify deployment: https://ocrio.elsondevops.cloud/

## Image Tags
- `latest`: Always points to the most recent build
- `<commit-sha>`: Specific version for rollback capability
