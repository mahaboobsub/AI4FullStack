#!/bin/bash
# ================================================================
# BloodBridge AI — Build & Deploy Script (run on EC2)
# ================================================================
# Usage: chmod +x deploy-app.sh && ./deploy-app.sh <YOUR_DOMAIN>
# Example: ./deploy-app.sh bloodbridge-api.duckdns.org
# ================================================================
set -euo pipefail

DOMAIN="${1:-}"
REPO_URL="https://github.com/mahaboobsub/AI4FullStack.git"
APP_DIR="/home/ubuntu/app/AI4FullStack"
FRONTEND_DIR="$APP_DIR/BloodBridge_AI_frontend"
BACKEND_DIR="$APP_DIR/BloodBridge_AI_Backend"
WEB_ROOT="/var/www/bloodbridge"

if [ -z "$DOMAIN" ]; then
    echo "ERROR: Please provide your domain as argument"
    echo "Usage: ./deploy-app.sh YOUR_DOMAIN"
    echo "Example: ./deploy-app.sh bloodbridge-api.duckdns.org"
    exit 1
fi

echo "============================================================"
echo "  BloodBridge AI — Deploy to $DOMAIN"
echo "============================================================"

# ── 1. Clone or Pull Repo ───────────────────────────────────────
echo ""
echo "[1/6] Getting latest code from GitHub..."
if [ -d "$APP_DIR" ]; then
    echo "  Repo exists, pulling latest..."
    cd "$APP_DIR"
    git pull origin main
else
    echo "  Cloning fresh repo..."
    mkdir -p /home/ubuntu/app
    cd /home/ubuntu/app
    git clone "$REPO_URL"
fi

# ── 2. Build Frontend ───────────────────────────────────────────
echo ""
echo "[2/6] Building React frontend..."
cd "$FRONTEND_DIR"

# Set the API URL to same-origin (frontend and backend on same domain)
# No VITE_API_URL needed — the frontend defaults to same-origin when empty
echo "VITE_API_URL=" > artifacts/bloodbridge/.env.production
echo "BASE_PATH=/" >> artifacts/bloodbridge/.env.production

pnpm install --frozen-lockfile 2>/dev/null || pnpm install
cd artifacts/bloodbridge
pnpm build

echo "  ✅ Frontend built successfully"

# ── 3. Deploy Frontend to Nginx ─────────────────────────────────
echo ""
echo "[3/6] Deploying frontend to web root..."
sudo rm -rf "$WEB_ROOT"/*
sudo cp -r dist/public/* "$WEB_ROOT"/
sudo chown -R www-data:www-data "$WEB_ROOT"

echo "  ✅ Frontend deployed to $WEB_ROOT"

# ── 4. Build Backend Docker Image ────────────────────────────────
echo ""
echo "[4/6] Building backend Docker image..."
cd "$BACKEND_DIR"
docker build -t bloodbridge-backend:latest .

echo "  ✅ Docker image built"

# ── 5. Check .env file exists ────────────────────────────────────
echo ""
echo "[5/6] Checking environment configuration..."
ENV_FILE="$BACKEND_DIR/.env.production"

if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "  ⚠️  No .env.production file found!"
    echo "  Create it now:"
    echo "    nano $ENV_FILE"
    echo ""
    echo "  Copy your environment variables into it, then re-run this script."
    echo "  See deploy/.env.production.template for all required variables."
    exit 1
fi

echo "  ✅ .env.production found"

# ── 6. Start/Restart Backend Container ───────────────────────────
echo ""
echo "[6/6] Starting backend container..."

# Stop existing container if running
docker stop bloodbridge 2>/dev/null || true
docker rm bloodbridge 2>/dev/null || true

# Run new container
docker run -d \
    --name bloodbridge \
    --env-file "$ENV_FILE" \
    -p 8000:8000 \
    --restart unless-stopped \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    bloodbridge-backend:latest

echo "  ✅ Backend container started"

# Wait for backend to be ready
echo ""
echo "  Waiting for backend health check..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✅ Backend is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  ⚠️  Backend didn't become healthy in 30s. Check logs:"
        echo "    docker logs bloodbridge"
        exit 1
    fi
    sleep 1
done

# ── Done ─────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ✅ DEPLOYMENT COMPLETE!"
echo "============================================================"
echo ""
echo "  Backend:  http://localhost:8000/health"
echo "  Frontend: http://$DOMAIN (after Nginx + SSL setup)"
echo ""
echo "  Next: Configure Nginx and SSL (see deployment guide)"
echo "============================================================"
