#!/bin/bash
# Installation script for Google Cloud

echo "=========================================="
echo "Installing Australian Trading Bot"
echo "=========================================="
echo ""

# Install Python packages
echo "[1/3] Installing Python packages..."
pip3 install -r requirements.txt --quiet

# Copy .env template if .env doesn't exist
if [ ! -f .env ]; then
    echo "[2/3] Creating .env file..."
    cp .env.template .env
    echo ""
    echo "IMPORTANT: Edit .env file and add your Binance API keys!"
    echo "Run: nano .env"
else
    echo "[2/3] .env file already exists"
fi

# Make start script executable
echo "[3/3] Setting permissions..."
chmod +x start.sh

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Add your Binance API keys"
echo "3. Run bot: ./start.sh"
echo ""
