#!/bin/bash

# Run this script on your EC2 self-hosted runner
# SSH: ssh -i "/Users/elsonpealias/us-east-1elson96.pem" ubuntu@ec2-54-205-104-13.compute-1.amazonaws.com -p1243

echo "🔧 Setting up GitHub Actions Self-Hosted Runner..."

# Update system
sudo apt-get update

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

# Install AWS CLI if not present
if ! command -v aws &> /dev/null; then
    echo "📦 Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Install kubectl if not present
if ! command -v kubectl &> /dev/null; then
    echo "📦 Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
fi

# Verify installations
echo ""
echo "✅ Verifying installations..."
docker --version
aws --version
kubectl version --client

echo ""
echo "✅ Runner setup complete!"
echo ""
echo "⚠️  IMPORTANT: Log out and log back in for Docker group changes to take effect"
echo "Then configure AWS credentials: aws configure"
