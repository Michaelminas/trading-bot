#!/bin/bash
# ONE-COMMAND INSTALL - Run this on your Google Cloud VM
# Usage: curl -sSL https://your-url/quick_install.sh | bash
# OR copy-paste this entire file into VM terminal

echo "=========================================="
echo "Installing Australian Trading Bot"
echo "=========================================="
echo ""

# Create directory
mkdir -p ~/trading-bot
cd ~/trading-bot

# Install dependencies
echo "[1/5] Installing Python packages..."
pip3 install ccxt pandas numpy python-dotenv --quiet

# Create .env file
echo "[2/5] Creating .env file..."
cat > .env << 'EOF'
BINANCE_API_KEY=hvauByIIGevOhVN7XdfdSTuUKAxV2rGc21J67yKWZTzc2HpDTkE0GZWUVkNzn3Ok
BINANCE_SECRET=mjIT08C2FL1Up3vS9XQ4n2iqBJGjzAwcxiatDnxwcgyX17cU6oN1j7K8CosxiWRI
EOF

# Create requirements.txt
echo "[3/5] Creating requirements.txt..."
cat > requirements.txt << 'EOF'
ccxt>=4.0.0
pandas>=2.0.0
numpy>=1.24.0
python-dotenv>=1.0.0
EOF

# Download trading bot (we'll paste the content)
echo "[4/5] Creating trading bot..."
echo "Paste trading_bot.py content here or upload separately"

# Create start script
echo "[5/5] Creating start script..."
cat > start.sh << 'EOFSTART'
#!/bin/bash
screen -dmS trading_bot python3 trading_bot.py
echo "[OK] Bot started in background"
echo "View: screen -r trading_bot"
echo "Detach: Ctrl+A then D"
EOFSTART

chmod +x start.sh

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next: Upload trading_bot.py to ~/trading-bot/"
echo "Then: ./start.sh"
echo ""
