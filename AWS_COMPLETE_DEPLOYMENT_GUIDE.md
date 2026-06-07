# 🩸 BloodBridge AI — Complete AWS Deployment Guide

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Architecture                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐        ┌──────────────────────────┐    │
│  │  CloudFront     │◄─────► │  S3 (Frontend)           │    │
│  │  (CDN)          │        │  - React App             │    │
│  │  - HTTPS        │        │  - Static Assets         │    │
│  │  - Caching      │        │  - SPA Config            │    │
│  └─────────────────┘        └──────────────────────────┘    │
│                                                               │
│  ┌─────────────────┐        ┌──────────────────────────┐    │
│  │  ALB / API GW   │        │  ECS Fargate/EC2         │    │
│  │  - Routing      │◄─────► │  (Backend)               │    │
│  │  - SSL/TLS      │        │  - FastAPI App           │    │
│  └─────────────────┘        │  - Docker Container      │    │
│           ▲                  │  - Auto-scaling          │    │
│           │                  └──────────────────────────┘    │
│           │                                                   │
│  ┌────────▼──────────────────────────────────────────────┐  │
│  │           External Databases (Free Tier)              │  │
│  │  • Supabase PostgreSQL (external)                     │  │
│  │  • Neo4j Aura (external)                              │  │
│  │  • ElastiCache (optional, for sessions)               │  │
│  └─────────────────────────────────────────────────────  ┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Supporting AWS Services                             │   │
│  │  • CloudWatch (Logging & Monitoring)                 │   │
│  │  • ECR (Docker Registry)                             │   │
│  │  • CloudFormation (IaC optional)                      │   │
│  │  • Route53 (DNS - optional)                           │   │
│  │  • Secrets Manager (Environment vars)                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 **Part 1: Backend Deployment (ECS Fargate)**

### 1.1 Prerequisites

- AWS Account with free tier access (12 months)
- AWS CLI installed and configured
- Docker installed locally
- GitHub/GitLab repository with source code

### 1.2 Step 1: Prepare Environment Variables

Create `.env` file in `BloodBridge_AI_Backend/`:

```bash
# Application
APP_ENV=production
LOG_LEVEL=info
DEBUG=false

# Supabase (external)
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJ... (anon key)
SUPABASE_SERVICE_KEY=eyJ... (service_role key)

# Neo4j Aura (external)
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-generated-password

# LLM Providers
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_WEBHOOK_SECRET=my_random_secret_32chars

# Optional: Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_FROM_NUMBER=+15551234567

# Optional: Vapi
VAPI_API_KEY=your_vapi_key
VAPI_ASSISTANT_ID=your_assistant_id

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2

# Security
CORS_ORIGINS=["https://yourdomain.com", "http://localhost:3000"]
CSRF_ENABLED=true
RATE_LIMIT_ENABLED=true
```

### 1.3 Step 2: Create AWS ECR Repository

```bash
# Set your AWS region and account details
export AWS_REGION=ap-south-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repository
aws ecr create-repository \
  --repository-name bloodbridge-backend \
  --region $AWS_REGION

# Output should include repository URI like:
# 123456789.dkr.ecr.ap-south-1.amazonaws.com/bloodbridge-backend
```

### 1.4 Step 3: Build & Push Docker Image

```bash
# Navigate to backend directory
cd BloodBridge_AI_Backend

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build image
docker build -t bloodbridge-backend:latest .

# Tag for ECR
docker tag bloodbridge-backend:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/bloodbridge-backend:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/bloodbridge-backend:latest

# Verify
aws ecr list-images --repository-name bloodbridge-backend --region $AWS_REGION
```

### 1.5 Step 4: Set Up ECS Cluster

**Option A: Using AWS Console (Recommended for beginners)**

1. Go to **ECS** → **Clusters** → **Create Cluster**
2. Name: `bloodbridge-prod`
3. Infrastructure: **Fargate** (serverless, pay-per-use)
4. Click **Create**

**Option B: Using AWS CLI**

```bash
aws ecs create-cluster \
  --cluster-name bloodbridge-prod \
  --region $AWS_REGION
```

### 1.6 Step 5: Create ECS Task Definition

Create file `ecs-task-definition.json`:

```json
{
  "family": "bloodbridge-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "bloodbridge-backend",
      "image": "123456789.dkr.ecr.ap-south-1.amazonaws.com/bloodbridge-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "APP_ENV",
          "value": "production"
        },
        {
          "name": "API_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "API_PORT",
          "value": "8000"
        }
      ],
      "secrets": [
        {
          "name": "SUPABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/supabase-url"
        },
        {
          "name": "SUPABASE_KEY",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/supabase-key"
        },
        {
          "name": "NEO4J_URI",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/neo4j-uri"
        },
        {
          "name": "NEO4J_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/neo4j-password"
        },
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/groq-api-key"
        },
        {
          "name": "GOOGLE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/google-api-key"
        },
        {
          "name": "TELEGRAM_BOT_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/telegram-token"
        },
        {
          "name": "TELEGRAM_WEBHOOK_SECRET",
          "valueFrom": "arn:aws:secretsmanager:ap-south-1:123456789:secret:bloodbridge/telegram-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/bloodbridge-backend",
          "awslogs-region": "ap-south-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole"
}
```

Register the task definition:

```bash
# Replace 123456789 with your AWS account ID
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json \
  --region $AWS_REGION
```

### 1.7 Step 6: Store Secrets in AWS Secrets Manager

```bash
# Create secrets for sensitive data
aws secretsmanager create-secret \
  --name bloodbridge/supabase-url \
  --secret-string "https://xxxxxxxxxxxx.supabase.co" \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name bloodbridge/supabase-key \
  --secret-string "eyJ..." \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name bloodbridge/neo4j-uri \
  --secret-string "neo4j+s://xxxxxxxx.databases.neo4j.io" \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name bloodbridge/neo4j-password \
  --secret-string "your-password" \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name bloodbridge/groq-api-key \
  --secret-string "gsk_..." \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name bloodbridge/google-api-key \
  --secret-string "AIza..." \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name bloodbridge/telegram-token \
  --secret-string "123456789:ABCdef..." \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name bloodbridge/telegram-secret \
  --secret-string "my_random_secret_32chars" \
  --region $AWS_REGION
```

### 1.8 Step 7: Create Application Load Balancer (ALB)

**Via AWS Console:**

1. Go to **EC2** → **Load Balancers** → **Create Load Balancer**
2. Choose **Application Load Balancer**
3. Configure:
   - Name: `bloodbridge-alb`
   - Scheme: Internet-facing
   - IP address type: IPv4
4. Select all availability zones in your region
5. Create security group allowing:
   - Inbound: 80 (HTTP), 443 (HTTPS)
   - Outbound: All to any
6. Create target group:
   - Name: `bloodbridge-targets`
   - Protocol: HTTP
   - Port: 8000
   - Health check path: `/api/health`
   - Health check interval: 30 seconds

### 1.9 Step 8: Create ECS Service

```bash
# Create VPC and subnets first (or use default)
export SUBNET_ID_1=subnet-xxxxx
export SUBNET_ID_2=subnet-xxxxx
export SECURITY_GROUP_ID=sg-xxxxx
export TARGET_GROUP_ARN=arn:aws:elasticloadbalancing:...

aws ecs create-service \
  --cluster bloodbridge-prod \
  --service-name bloodbridge-backend-service \
  --task-definition bloodbridge-backend:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID_1,$SUBNET_ID_2],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=$TARGET_GROUP_ARN,containerName=bloodbridge-backend,containerPort=8000 \
  --region $AWS_REGION
```

### 1.10 Step 9: Set Up HTTPS with ACM

1. Go to **AWS Certificate Manager** → **Request a certificate**
2. Domain names: `api.yourdomain.com`, `yourdomain.com`
3. Validation: DNS (add CNAME records from your DNS provider)
4. Wait for validation (~5 minutes)
5. Add to ALB listener (HTTPS:443 → Target Group)

### 1.11 Step 10: Enable Auto-scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/bloodbridge-prod/bloodbridge-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 4 \
  --region $AWS_REGION

# Create scaling policy (scale up when CPU > 70%)
aws application-autoscaling put-scaling-policy \
  --policy-name bloodbridge-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/bloodbridge-prod/bloodbridge-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration "TargetValue=70.0,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}" \
  --region $AWS_REGION
```

### 1.12 Verify Backend Deployment

```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --names bloodbridge-alb \
  --region $AWS_REGION \
  --query 'LoadBalancers[0].DNSName'

# Test health endpoint
curl http://bloodbridge-alb-123456.ap-south-1.elb.amazonaws.com/api/health

# Check ECS service
aws ecs describe-services \
  --cluster bloodbridge-prod \
  --services bloodbridge-backend-service \
  --region $AWS_REGION
```

---

## 🎨 **Part 2: Frontend Deployment (S3 + CloudFront)**

### 2.1 Build Frontend

```bash
cd BloodBridge_AI_frontend

# Install dependencies
pnpm install

# Build for production
pnpm build

# Output should be in artifacts/bloodbridge/dist or similar
```

### 2.2 Create S3 Bucket

```bash
export BUCKET_NAME=bloodbridge-frontend-$RANDOM

aws s3 mb s3://$BUCKET_NAME \
  --region $AWS_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Block public access (we'll use CloudFront)
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2.3 Create CloudFront Distribution

Create file `cloudfront-config.json`:

```json
{
  "CallerReference": "bloodbridge-frontend-$(date +%s)",
  "Comment": "BloodBridge AI Frontend Distribution",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3Origin",
        "DomainName": "bloodbridge-frontend-xxxxx.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TargetOriginId": "S3Origin",
    "Compress": true
  },
  "CacheBehaviors": [
    {
      "PathPattern": "/api/*",
      "AllowedMethods": {
        "Quantity": 7,
        "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      },
      "CachePolicyId": "4135ea3d-c35d-46eb-81d7-reused0EXAMPLEID",
      "OriginRequestPolicyId": "216adef5-5c7f-47e4-b989-5492eafa07d3",
      "ViewerProtocolPolicy": "https-only",
      "TargetOriginId": "ALBOrigin"
    }
  ],
  "CustomErrorResponses": [
    {
      "ErrorCode": 404,
      "ResponsePagePath": "/index.html",
      "ResponseCode": "200",
      "ErrorCachingMinTTL": 300
    },
    {
      "ErrorCode": 403,
      "ResponsePagePath": "/index.html",
      "ResponseCode": "200",
      "ErrorCachingMinTTL": 300
    }
  ],
  "DefaultRootObject": "index.html"
}
```

Create CloudFront distribution:

```bash
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json \
  --region $AWS_REGION
```

### 2.4 Upload Frontend to S3

```bash
# Navigate to build directory
cd artifacts/bloodbridge/dist

# Sync to S3 (with cache headers)
aws s3 sync . s3://$BUCKET_NAME/ \
  --delete \
  --cache-control "max-age=31536000,public" \
  --exclude "index.html" \
  --exclude ".html"

# index.html should not be cached
aws s3 cp index.html s3://$BUCKET_NAME/ \
  --cache-control "no-cache,no-store,must-revalidate"

# Verify upload
aws s3 ls s3://$BUCKET_NAME/ --recursive
```

### 2.5 Configure Domain (Route53) - Optional

```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone \
  --name yourdomain.com \
  --caller-reference $(date +%s)

# Create alias record pointing to CloudFront
# Get CloudFront domain name
export CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
  --id YOUR_DISTRIBUTION_ID \
  --query 'Distribution.DomainName' \
  --output text)

# Create Route53 record (use AWS Console for easier management)
# Point yourdomain.com → CloudFront domain
```

### 2.6 Update Backend API Endpoints

In your frontend code, update API base URL:

```typescript
// src/config/api.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.yourdomain.com';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

Build and redeploy:

```bash
pnpm build
aws s3 sync dist/ s3://$BUCKET_NAME/ --delete
```

---

## 🔐 **Part 3: Security & Monitoring**

### 3.1 CloudWatch Logs

Logs are automatically sent from ECS to CloudWatch. View them:

```bash
# Get logs
aws logs tail /ecs/bloodbridge-backend --follow

# Create log insights query
aws logs start-query \
  --log-group-name /ecs/bloodbridge-backend \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | stats count()'
```

### 3.2 CloudWatch Alarms

```bash
# Alarm for high CPU
aws cloudwatch put-metric-alarm \
  --alarm-name bloodbridge-high-cpu \
  --alarm-description "Alert when ECS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:ap-south-1:123456789:your-sns-topic

# Alarm for ALB unhealthy targets
aws cloudwatch put-metric-alarm \
  --alarm-name bloodbridge-unhealthy-targets \
  --alarm-description "Alert when targets become unhealthy" \
  --metric-name UnHealthyHostCount \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold
```

### 3.3 WAF (Web Application Firewall) - Optional

```bash
# Create WAF web ACL for CloudFront
aws wafv2 create-web-acl \
  --name bloodbridge-waf \
  --scope CLOUDFRONT \
  --default-action Block={} \
  --rules '[
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 0,
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "AWSManagedRulesCommonRuleSetMetric"},
      "Statement": {"ManagedRuleGroupStatement": {"VendorName": "AWS", "Name": "AWSManagedRulesCommonRuleSet"}}
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=bloodbridge-waf
```

### 3.4 Enable VPC Flow Logs

```bash
# Get VPC ID
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)

# Create IAM role for VPC Flow Logs
aws iam create-role \
  --role-name vpc-flow-logs-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Create VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $VPC_ID \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs
```

---

## 💰 **Part 4: Cost Optimization**

### 4.1 AWS Free Tier Usage

| Service | Free Tier | Monthly Cost (Pay) |
|---------|-----------|-------------------|
| **ECS Fargate** | 750 compute hours | $0.04664/hour after |
| **S3** | 5 GB storage | $0.023/GB after |
| **CloudFront** | 1 TB bandwidth | $0.085/GB after |
| **ALB** | 750 hours | $0.0225/hour after |
| **CloudWatch** | 10 custom metrics | $0.10/metric after |
| **Secrets Manager** | N/A (paid) | $0.40/secret/month |

**Estimated monthly cost (with free tier):**
- ECS Fargate (1 task, t3.micro equiv): $0
- S3 (10 GB, 10M requests): $0
- CloudFront (100 GB/month): ~$8.50
- ALB: $0
- **Total: ~$10-15/month**

### 4.2 Cost Reduction Tips

```bash
# 1. Use Lambda instead of ECS for lightweight tasks
# 2. Enable S3 Intelligent-Tiering for older objects
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket $BUCKET_NAME \
  --id auto-archive \
  --intelligent-tiering-configuration '{"Id":"auto-archive","Filter":{"Prefix":""},"Status":"Enabled","Tierings":[{"Days":90,"AccessTier":"ARCHIVE_ACCESS"},{"Days":180,"AccessTier":"DEEP_ARCHIVE_ACCESS"}]}'

# 3. Set lifecycle policy for CloudFront logs
# 4. Use Reserved Capacity for predictable workloads
# 5. Consolidate services (e.g., use RDS instead of external Supabase)
```

### 4.3 Estimated Bill Breakdown

```
┌──────────────────────────────────┬────────────┬─────────────┐
│ Service                          │ Free Tier  │ Overage     │
├──────────────────────────────────┼────────────┼─────────────┤
│ EC2 (t3.micro, 750 hrs)          │ FREE       │ $0.0104/hr  │
│ ECS Fargate (750 hrs)            │ FREE       │ $0.04664/hr │
│ S3 (5 GB, 20K GET)               │ FREE       │ $0.023/GB   │
│ CloudFront (1 TB egress)         │ FREE       │ $0.085/GB   │
│ ALB (750 hrs)                    │ FREE       │ $0.0225/hr  │
│ CloudWatch (10 metrics)          │ FREE       │ $0.10/extra │
│ Secrets Manager                  │ N/A        │ $0.40/month │
├──────────────────────────────────┼────────────┼─────────────┤
│ TOTAL (12-month free tier)       │ ~$0        │ N/A         │
│ TOTAL (post free tier)           │ ~$20-30    │ Per month   │
└──────────────────────────────────┴────────────┴─────────────┘
```

---

## 🚀 **Part 5: CI/CD Pipeline (GitHub Actions)**

### 5.1 Create GitHub Actions Workflow

Create file `.github/workflows/deploy.yml`:

```yaml
name: Deploy BloodBridge to AWS

on:
  push:
    branches:
      - main
      - production
  pull_request:
    branches:
      - main

env:
  AWS_REGION: ap-south-1
  ECR_REPOSITORY: bloodbridge-backend
  ECS_SERVICE: bloodbridge-backend-service
  ECS_CLUSTER: bloodbridge-prod

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build Docker image
        working-directory: ./BloodBridge_AI_Backend
        run: |
          docker build -t ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }} .
          docker tag ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }} ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest

      - name: Push image to ECR
        run: |
          docker push ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          docker push ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest

      - name: Update ECS task definition
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: BloodBridge_AI_Backend/ecs-task-definition.json
          container-name: bloodbridge-backend
          image: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}

      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true

      - name: Deploy frontend to S3
        if: github.ref == 'refs/heads/main'
        working-directory: ./BloodBridge_AI_frontend
        run: |
          pnpm install
          pnpm build
          aws s3 sync artifacts/bloodbridge/dist s3://${{ secrets.S3_BUCKET_NAME }}/ --delete

      - name: Invalidate CloudFront cache
        if: github.ref == 'refs/heads/main'
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

### 5.2 Add GitHub Secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=bloodbridge-frontend-xxxxx
CLOUDFRONT_DISTRIBUTION_ID=E123ABC...
```

---

## 📊 **Part 6: Monitoring & Logging**

### 6.1 Set Up CloudWatch Dashboard

```bash
aws cloudwatch put-dashboard \
  --dashboard-name bloodbridge-dashboard \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
            [".", "MemoryUtilization"],
            ["AWS/ApplicationELB", "TargetResponseTime"],
            [".", "RequestCount"],
            ["AWS/CloudFront", "BytesDownloaded"],
            [".", "Requests"]
          ],
          "period": 300,
          "stat": "Average",
          "region": "ap-south-1",
          "title": "BloodBridge Performance"
        }
      }
    ]
  }'
```

### 6.2 Set Up Alerts with SNS

```bash
# Create SNS topic
aws sns create-topic --name bloodbridge-alerts

# Subscribe to email
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-south-1:123456789:bloodbridge-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

---

## 🧪 **Part 7: Testing & Validation**

### 7.1 Test Backend Health

```bash
# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names bloodbridge-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

# Test health endpoint
curl -X GET http://$ALB_DNS/api/health

# Test with auth
curl -X GET http://$ALB_DNS/api/donors/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7.2 Load Testing

```bash
# Using Apache Bench
ab -n 100 -c 10 http://$ALB_DNS/api/health

# Using wrk
wrk -t4 -c100 -d30s http://$ALB_DNS/api/health
```

### 7.3 Test Telegram Webhook

```bash
# Set webhook
WEBHOOK_URL="https://api.yourdomain.com/api/webhooks/telegram"

curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "'$WEBHOOK_URL'", "secret_token": "'$TELEGRAM_WEBHOOK_SECRET'"}'

# Verify
curl -X GET "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

---

## 📝 **Part 8: Post-Deployment Checklist**

- [ ] Backend running on ECS with health checks passing
- [ ] Frontend accessible via CloudFront CDN
- [ ] SSL/TLS certificates valid
- [ ] Environment variables loaded from Secrets Manager
- [ ] Database connections working (Supabase + Neo4j)
- [ ] Telegram webhook configured and receiving messages
- [ ] CloudWatch logs streaming properly
- [ ] Auto-scaling policies in place
- [ ] CloudFront cache invalidation working
- [ ] Route53 DNS configured (if using custom domain)
- [ ] Backup strategy for databases implemented
- [ ] Monitoring alerts configured
- [ ] Cost anomaly detection enabled

---

## 🆘 **Troubleshooting**

### Backend not responding

```bash
# Check ECS service
aws ecs describe-services \
  --cluster bloodbridge-prod \
  --services bloodbridge-backend-service

# Check task logs
aws ecs list-tasks --cluster bloodbridge-prod
TASK_ARN=$(aws ecs list-tasks --cluster bloodbridge-prod --query 'taskArns[0]' --output text)
aws logs tail /ecs/bloodbridge-backend --follow
```

### CloudFront not showing updates

```bash
# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### Secrets not loading

```bash
# Verify IAM role has Secrets Manager permissions
aws iam list-attached-role-policies --role-name ecsTaskExecutionRole

# Check secret exists
aws secretsmanager get-secret-value \
  --secret-id bloodbridge/groq-api-key \
  --region ap-south-1
```

---

## 📚 **Additional Resources**

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/welcome.html)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)
- [Supabase Deployment](https://supabase.com/docs)
- [Neo4j Aura](https://neo4j.com/cloud/platform/aura/)

---

**Last Updated:** June 2026
**Status:** Complete
