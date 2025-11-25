#!/bin/bash
set -e

IMAGE_NAME="ocrapp-elsondevops"
TAG="latest"
DOCKERHUB_USER="${DOCKERHUB_USER:-your-dockerhub-username}"
ECR_REGISTRY="739275449845.dkr.ecr.us-east-1.amazonaws.com"
ECR_REPO="${ECR_REGISTRY}/${IMAGE_NAME}"

echo "Building Docker image for ARM64..."
docker buildx build --platform linux/arm64 -t ${IMAGE_NAME}:${TAG} .

echo "Tagging for Docker Hub..."
docker tag ${IMAGE_NAME}:${TAG} ${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}

echo "Tagging for ECR..."
docker tag ${IMAGE_NAME}:${TAG} ${ECR_REPO}:${TAG}

echo "Logging into ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo "Pushing to Docker Hub..."
docker push ${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}

echo "Pushing to ECR..."
docker push ${ECR_REPO}:${TAG}

echo "✅ Build and push complete!"
echo "Docker Hub: ${DOCKERHUB_USER}/${IMAGE_NAME}:${TAG}"
echo "ECR: ${ECR_REPO}:${TAG}"
