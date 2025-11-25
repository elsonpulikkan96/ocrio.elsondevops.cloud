#!/bin/bash
set -e

CLUSTER_NAME="ocrapp-elsondevops-app"
REGION="us-east-1"
NODE_TYPE="t4g.medium"  # ARM64 instance type
NODE_COUNT=2

echo "Creating EKS cluster: ${CLUSTER_NAME}..."
eksctl create cluster \
  --name ${CLUSTER_NAME} \
  --region ${REGION} \
  --nodegroup-name ocrapp-nodes \
  --node-type ${NODE_TYPE} \
  --nodes ${NODE_COUNT} \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed

echo "Installing AWS Load Balancer Controller..."
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

eksctl create iamserviceaccount \
  --cluster=${CLUSTER_NAME} \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
  --override-existing-serviceaccounts \
  --approve

helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=${CLUSTER_NAME} \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

echo "✅ EKS cluster setup complete!"
echo "Cluster: ${CLUSTER_NAME}"
echo "Region: ${REGION}"
