# OCR IO - Advanced Image to Text Converter

Enterprise-grade OCR application with intelligent multi-method processing, QR/barcode detection, and automatic text validation. Deployed on AWS EKS with no rate limits or file size restrictions.

## 🌐 Live Application

**URL**: https://ocrio.elsondevops.cloud

## ✨ Features

- **Multi-Method OCR**: Tries 4 different preprocessing methods and returns the best result
- **QR/Barcode Detection**: Automatic detection and decoding of QR codes and barcodes
- **Text Validation**: Filters garbled text automatically, ensures readable output
- **All Image Formats**: JPG, JPEG, PNG, GIF, BMP, TIFF, WebP, HEIC
- **Multi-Language Support**: Powered by Tesseract OCR engine
- **No Limits**: Unlimited file size, no rate limits, no usage restrictions
- **Privacy First**: No data storage, no transmission, no tracking
- **Production Ready**: Deployed on AWS EKS with HTTPS and SSL

## 🏗️ Architecture

```
User → Route 53 → ALB (HTTPS) → EKS Cluster → Pods (Multi-Method OCR)
```

### Technology Stack

- **Base Image**: Python 3.11 Debian Slim (ARM64)
- **Backend**: FastAPI + Tesseract OCR + OpenCV
- **Frontend**: Vanilla HTML/CSS/JS with drag-and-drop
- **Image Processing**: PIL, OpenCV, NumPy
- **Barcode Detection**: pyzbar
- **Container**: Docker (ARM64)
- **Orchestration**: AWS EKS (t4g.medium ARM64 nodes)
- **Load Balancer**: Application Load Balancer with 300s timeout
- **SSL**: AWS ACM (*.elsondevops.cloud)
- **DNS**: Route 53

## 🎯 How It Works

### Multi-Method OCR Processing

The application tries 4 different preprocessing methods:

1. **Otsu's Binary Thresholding** + Denoising
2. **Adaptive Gaussian Thresholding**
3. **CLAHE** (Contrast Limited Adaptive Histogram Equalization) + Morphology
4. **Minimal Processing** (grayscale only)

Each method runs OCR independently, validates the result, and the system returns the longest valid text.

### Text Validation

- Checks if >50% characters are alphanumeric
- Rejects results with >30% special characters
- Filters garbled lines automatically
- Cleans excessive whitespace

## 📦 Project Structure

```
ocrio.elsondevops.cloud/
├── app/
│   └── main.py              # FastAPI application with multi-method OCR
├── frontend/
│   └── index.html           # Clean UI with drag-and-drop
├── k8s/
│   ├── deployment.yaml      # Kubernetes deployment (2 replicas)
│   ├── service.yaml         # ClusterIP service
│   └── ingress.yaml         # ALB ingress with SSL
├── Dockerfile               # Debian-based ARM64 image
├── requirements.txt         # Python dependencies
├── build-push.sh           # Build and push to ECR
├── deploy.sh               # Deploy to EKS
├── setup-eks.sh            # Create EKS cluster
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker with buildx (ARM64 support)
- AWS CLI configured
- kubectl installed
- eksctl (for cluster management)
- Helm (for AWS Load Balancer Controller)

### 1. Create EKS Cluster (First Time Only)

```bash
./setup-eks.sh
```

This creates:
- EKS cluster: `ocrapp-elsondevops-app`
- Node group: t4g.medium ARM64 instances
- AWS Load Balancer Controller

### 2. Build and Push Image

```bash
./build-push.sh
```

Builds ARM64 image and pushes to:
- ECR: `739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops:latest`

### 3. Deploy to EKS

```bash
./deploy.sh
```

Deploys:
- 2 pod replicas
- ClusterIP service
- ALB ingress with HTTPS

### 4. Verify Deployment

```bash
kubectl get pods,svc,ingress -l app=ocrapp-elsondevops
```

## 📊 AWS Resources

| Resource | Value |
|----------|-------|
| **EKS Cluster** | ocrapp-elsondevops-app |
| **Region** | us-east-1 |
| **ECR Repository** | 739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops |
| **ACM Certificate** | arn:aws:acm:us-east-1:739275449845:certificate/f5be8959-2f51-44b4-a827-6ca97cc45a98 |
| **Domain** | ocrio.elsondevops.cloud |
| **Node Type** | t4g.medium (ARM64) |
| **Replicas** | 2 |
| **ALB Timeout** | 300 seconds |

## 🔧 API Endpoints

### `GET /`
Returns the web interface

### `POST /api/ocr`
Upload image for OCR processing

**Request**: 
```bash
curl -X POST https://ocrio.elsondevops.cloud/api/ocr \
  -F "file=@image.jpg"
```

**Response**: 
```json
{
  "text": "=== QR CODES / BARCODES ===\n[QRCODE] https://example.com\n\n=== TEXT CONTENT ===\nExtracted text here..."
}
```

### `GET /health`
Health check endpoint

**Response**:
```json
{
  "status": "healthy",
  "version": "6.0.0",
  "engine": "Multi-Method OCR"
}
```

## 🧪 Local Development

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access at: http://localhost:8000

### Test OCR Endpoint

```bash
curl -X POST http://localhost:8000/api/ocr \
  -F "file=@test-image.jpg"
```

## 📦 Monitoring

### Check Pod Status
```bash
kubectl get pods -l app=ocrapp-elsondevops
```

### View Logs
```bash
kubectl logs -l app=ocrapp-elsondevops --tail=50 -f
```

### Check Ingress
```bash
kubectl describe ingress ocrapp-elsondevops-ingress
```

### Check Target Health
```bash
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN> \
  --region us-east-1
```

## 🔄 Update Deployment

After making code changes:

```bash
# Rebuild image
docker buildx build --platform linux/arm64 -t ocrapp-elsondevops:latest --load .

# Push to ECR
docker tag ocrapp-elsondevops:latest 739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops:latest
docker push 739275449845.dkr.ecr.us-east-1.amazonaws.com/ocrapp-elsondevops:latest

# Restart deployment
kubectl rollout restart deployment ocrapp-elsondevops
kubectl rollout status deployment ocrapp-elsondevops
```

## 🗑️ Cleanup

### Delete Application
```bash
kubectl delete -f k8s/
```

### Delete EKS Cluster
```bash
eksctl delete cluster --name ocrapp-elsondevops-app --region us-east-1
```

### Delete ECR Images
```bash
aws ecr batch-delete-image \
  --repository-name ocrapp-elsondevops \
  --region us-east-1 \
  --image-ids imageTag=latest
```

## 💡 Best Practices for OCR

For optimal results:
- Use high-resolution images (minimum 1500px)
- Ensure good lighting without shadows
- Avoid glare and reflections
- Keep text clear and in focus
- Scan documents at 300 DPI or higher
- Use clear, high-contrast images

## 🔒 Security

- HTTPS enforced with valid SSL certificate
- No data storage or logging
- Privacy-focused design
- No external API calls
- All processing happens in-memory

## 📈 Performance

- Processing time: 30-60 seconds for complex images
- Timeout: 300 seconds (5 minutes)
- Concurrent processing: 2 replicas
- Auto-scaling: Can be configured via HPA

## 🐛 Troubleshooting

### "Network error" message
- Wait for full processing time (up to 60s)
- Check internet connection
- Try a smaller/clearer image first
- Refresh page and retry

### Garbled text output
- Image quality may be too low
- Text too small or blurry
- Rescan document at higher resolution
- Ensure good lighting and focus

### Pods not starting
```bash
kubectl describe pod -l app=ocrapp-elsondevops
kubectl logs -l app=ocrapp-elsondevops
```

### Ingress not creating ALB
```bash
kubectl describe ingress ocrapp-elsondevops-ingress
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

## 📄 License

MIT License - Free to use and modify

## 🤝 Contributing

Contributions welcome! This is a privacy-focused, open-source OCR solution.

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review application logs
- Verify AWS resources are healthy

---

**Built with ❤️ for privacy-focused OCR processing**

**Live at**: https://ocrio.elsondevops.cloud
# CI/CD Pipeline Active - Fri Nov 28 17:40:26 IST 2025

# Trigger v8.0 deployment
