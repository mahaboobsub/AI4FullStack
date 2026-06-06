# BloodBridge AI — AWS Deployment Guide (A7 + A8 + B7)

## 1. Backend — EC2 Deployment (A7)

### EC2 Instance
- **Type**: t3.micro (Amazon Linux 2023)
- **Ports**: 22 (SSH), 80, 443, 8000
- **Region**: ap-south-1

### Docker Setup
```bash
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# ECR Login
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

# Build and Push
docker build -t bloodbridge-backend .
docker tag bloodbridge-backend:latest <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/bloodbridge-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/bloodbridge-backend:latest

# Run
docker run -d --name bloodbridge --env-file .env -p 8000:8000 --restart unless-stopped bloodbridge-backend:latest
```

### Nginx Reverse Proxy
```bash
sudo yum install -y nginx
sudo cp nginx/bloodbridge.conf /etc/nginx/conf.d/
sudo systemctl enable nginx
sudo systemctl start nginx

# TLS with Certbot
sudo yum install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.bloodbridge.ai
```

### Health Check
```bash
curl https://api.bloodbridge.ai/api/health
# Must return 200 with all services online
```

---

## 2. Telegram Webhook — Permanent HTTPS (A8)

### Setup
```bash
# After EC2 + nginx + TLS are running:
python setup_webhook.py

# Verify
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

### systemd Service
```ini
# /etc/systemd/system/bloodbridge.service
[Unit]
Description=BloodBridge AI Backend
After=docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=/usr/bin/docker start -a bloodbridge
ExecStop=/usr/bin/docker stop bloodbridge
Restart=on-failure
RestartSec=5
ExecStartPost=/bin/bash -c 'sleep 10 && python3 /app/setup_webhook.py'

[Install]
WantedBy=multi-user.target
```

---

## 3. Frontend — S3 + CloudFront (B7)

### S3 Bucket
```bash
# Create bucket
aws s3 mb s3://bloodbridge-frontend --region ap-south-1

# Enable static hosting
aws s3 website s3://bloodbridge-frontend --index-document index.html --error-document index.html
```

### CloudFront Distribution
- **Origin**: S3 website endpoint
- **Default root**: index.html
- **Custom error**: 403 → /index.html (200) for React Router
- **Price class**: PriceClass_100
- **Compression**: Enabled

### Deploy Script (deploy.sh)
```bash
#!/bin/bash
set -e

EC2_BACKEND_URL=${1:-"https://api.bloodbridge.ai"}
echo "VITE_API_URL=$EC2_BACKEND_URL" > .env.production

cd BloodBridge_AI_frontend
pnpm build

aws s3 sync dist/ s3://bloodbridge-frontend --delete
aws cloudfront create-invalidation --distribution-id $CF_DIST_ID --paths "/*"

echo "✅ Frontend deployed to CloudFront"
```

### Post-deploy
```bash
# Add CloudFront URL to backend ALLOWED_ORIGINS
# Restart container
docker restart bloodbridge
# Verify
curl -I https://<cloudfront-domain>/
```
