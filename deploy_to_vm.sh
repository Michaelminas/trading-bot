#!/bin/bash
# One-command deployment to your VM
# Usage: ./deploy_to_vm.sh your-vm-ip

if [ -z "$1" ]; then
    echo "Usage: ./deploy_to_vm.sh <vm-ip-address>"
    echo "Example: ./deploy_to_vm.sh 35.123.456.789"
    exit 1
fi

VM_IP=$1
VM_USER=${2:-$USER}  # Default to current username

echo "=========================================="
echo "Deploying to VM: $VM_IP"
echo "Username: $VM_USER"
echo "=========================================="
echo ""

# Create zip if not exists
if [ ! -f "../GOOGLE_CLOUD_DEPLOY.zip" ]; then
    echo "[1/4] Creating zip file..."
    cd ..
    zip -r GOOGLE_CLOUD_DEPLOY.zip GOOGLE_CLOUD_DEPLOY/ -x "*.pyc" -x "__pycache__/*" -x ".git/*"
    cd GOOGLE_CLOUD_DEPLOY
else
    echo "[1/4] Using existing zip file"
fi

# Upload to VM
echo "[2/4] Uploading to VM..."
scp ../GOOGLE_CLOUD_DEPLOY.zip $VM_USER@$VM_IP:~/

# SSH and install
echo "[3/4] Installing on VM..."
ssh $VM_USER@$VM_IP << 'ENDSSH'
    cd ~
    unzip -o GOOGLE_CLOUD_DEPLOY.zip
    cd GOOGLE_CLOUD_DEPLOY
    chmod +x install.sh start.sh
    ./install.sh
ENDSSH

# Start bot
echo "[4/4] Starting bot..."
ssh $VM_USER@$VM_IP << 'ENDSSH'
    cd ~/GOOGLE_CLOUD_DEPLOY
    ./start.sh
ENDSSH

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "To view bot:"
echo "  ssh $VM_USER@$VM_IP"
echo "  screen -r trading_bot"
echo ""
echo "To view logs:"
echo "  ssh $VM_USER@$VM_IP"
echo "  tail -f ~/GOOGLE_CLOUD_DEPLOY/trading_bot.log"
echo ""
