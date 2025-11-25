#!/bin/bash
set -e

CLUSTER_NAME="ocrapp-elsondevops-app"
REGION="us-east-1"

echo "Updating kubeconfig for EKS cluster..."
aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${REGION}

echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/ocrapp-elsondevops

echo "✅ Deployment complete!"
echo ""
echo "Get pods:"
echo "  kubectl get pods -l app=ocrapp-elsondevops"
echo ""
echo "Get service:"
echo "  kubectl get svc ocrapp-elsondevops-svc"
echo ""
echo "Get ingress:"
echo "  kubectl get ingress ocrapp-elsondevops-ingress"
echo ""
echo "View logs:"
echo "  kubectl logs -l app=ocrapp-elsondevops --tail=50 -f"
