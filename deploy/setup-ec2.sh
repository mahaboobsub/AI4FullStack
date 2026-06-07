#!/bin/bash
# ================================================================
# BloodBridge AI — EC2 Ubuntu Bootstrap Script
# ================================================================
# Run this ONCE on a fresh EC2 Ubuntu 24.04 instance.
# Usage: chmod +x setup-ec2.sh && sudo ./setup-ec2.sh
# ================================================================
set -euo pipefail

echo "============================================================"
echo "  BloodBridge AI — EC2 Setup Script"
echo "============================================================"

# ── 1. System Updates ────────────────────────────────────────────
echo ""
echo "[1/7] Updating system packages..."
apt-get update -y
apt-get upgrade -y

# ── 2. Docker ────────────────────────────────────────────────────
echo ""
echo "[2/7] Installing Docker..."
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker

# Allow ubuntu user to run docker without sudo
usermod -aG docker ubuntu

echo "  ✅ Docker installed: $(docker --version)"

# ── 3. Node.js 20 LTS + pnpm (for frontend build) ───────────────
echo ""
echo "[3/7] Installing Node.js 20 LTS + pnpm..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g pnpm@9

echo "  ✅ Node.js installed: $(node --version)"
echo "  ✅ pnpm installed: $(pnpm --version)"

# ── 4. Nginx ─────────────────────────────────────────────────────
echo ""
echo "[4/7] Installing Nginx..."
apt-get install -y nginx
systemctl enable nginx

echo "  ✅ Nginx installed: $(nginx -v 2>&1)"

# ── 5. Certbot (Let's Encrypt SSL) ──────────────────────────────
echo ""
echo "[5/7] Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

echo "  ✅ Certbot installed: $(certbot --version 2>&1)"

# ── 6. Swap Space (2GB — prevents OOM during Docker build) ──────
echo ""
echo "[6/7] Creating 2GB swap file..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "  ✅ 2GB swap created and activated"
else
    echo "  ℹ️  Swap file already exists, skipping"
fi

# ── 7. Create directories ───────────────────────────────────────
echo ""
echo "[7/7] Creating application directories..."
mkdir -p /var/www/bloodbridge
mkdir -p /var/www/certbot
mkdir -p /home/ubuntu/app

chown -R ubuntu:ubuntu /home/ubuntu/app
chown -R www-data:www-data /var/www/bloodbridge

echo "  ✅ Directories created"

# ── Done ─────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ✅ EC2 SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "  Installed: Docker, Node.js 20, pnpm 9, Nginx, Certbot"
echo "  Swap:      2GB (prevents OOM during builds)"
echo ""
echo "  IMPORTANT: Log out and log back in for Docker group to take effect:"
echo "    exit"
echo "    ssh -i your-key.pem ubuntu@your-ec2-ip"
echo ""
echo "  Then proceed to clone your repo and deploy."
echo "============================================================"
