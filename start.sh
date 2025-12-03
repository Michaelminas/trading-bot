#!/bin/bash
# Start trading bot with screen (keeps running after disconnect)

echo "=========================================="
echo "Starting Australian Trading Bot"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo "Please run: ./install.sh first"
    exit 1
fi

# Start bot in screen session
screen -dmS trading_bot python3 trading_bot.py

echo "[OK] Bot started in background"
echo ""
echo "Commands:"
echo "  View logs:     screen -r trading_bot"
echo "  Detach:        Ctrl+A then D"
echo "  Stop bot:      screen -X -S trading_bot quit"
echo "  View trades:   cat trades.csv"
echo "  View logs:     tail -f trading_bot.log"
echo ""
