# Deployment Guide

## Quick Start (3 Steps)

### 1. Create EKS Cluster (First Time Only)
```bash
./setup-eks.sh
```
**Time**: ~15 minutes

### 2. Build & Push Image
```bash
./build-push.sh
```
**Time**: ~5 minutes

### 3. Deploy Application
```bash
./deploy.sh
```
**Time**: ~2 minutes

---

## Verification

### Check Deployment Status
```bash
kubectl get pods,svc,ingress -l app=ocrapp-elsondevops
```

### Test Application
```bash
curl https://ocrio.elsondevops.cloud
```

### Access in Browser
Open: **https://ocrio.elsondevops.cloud**

---

## Update Application

After making code changes:

```bash
# Rebuild image
docker buildx build --platform linux/arm64 -t ocrapp-elsondevops:latest --load .

# Push to ECR
docker tag ocrapp-elsondevops:latest 739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops:latest
docker push 739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops:latest

# Restart pods
kubectl rollout restart deployment ocrapp-elsondevops
kubectl rollout status deployment ocrapp-elsondevops
```

---

## Monitoring

### View Logs
```bash
kubectl logs -l app=ocrapp-elsondevops --tail=100 -f
```

### Check Pod Status
```bash
kubectl describe pod -l app=ocrapp-elsondevops
```

### Check Target Health
```bash
aws elbv2 describe-target-health \
  --target-group-arn $(kubectl get ingress ocrapp-elsondevops-ingress -o jsonpath='{.metadata.annotations.alb\.ingress\.kubernetes\.io/target-group-arn}') \
  --region us-east-1
```

---

## Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod -l app=ocrapp-elsondevops
kubectl logs -l app=ocrapp-elsondevops
```

### Ingress Issues
```bash
kubectl describe ingress ocrapp-elsondevops-ingress
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

### Image Pull Errors
```bash
aws ecr describe-images --repository-name ocrapp-elsondevops --region us-east-1
```

---

## Cleanup

### Delete Application
```bash
kubectl delete -f k8s/
```

### Delete EKS Cluster
```bash
eksctl delete cluster --name ocrapp-elsondevops-app --region us-east-1
```

---

## Resources

- **URL**: https://ocrio.elsondevops.cloud
- **EKS Cluster**: ocrapp-elsondevops-app
- **Region**: us-east-1
- **ECR**: 739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops
