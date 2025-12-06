"""
TEST TRADE EXECUTION - Verify Bot Can Trade
This script tests the complete trade lifecycle:
1. Connect to Binance
2. Fetch market data
3. Place a small test buy order
4. Wait a moment
5. Place a sell order to close
6. Report results

Run this BEFORE starting the 4-week test to ensure everything works!
"""

import ccxt
import os
import time
from dotenv import load_dotenv

# Load API keys
load_dotenv()
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_SECRET')

print("="*80)
print("TRADE EXECUTION TEST - Paper Trading")
print("="*80)
print()

# Initialize exchange
print("[1/7] Connecting to Binance...")
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'},
})

# Enable testnet mode
print("[2/7] Enabling TESTNET mode...")
exchange.set_sandbox_mode(True)
print("      Mode: TESTNET (Paper Trading)")
print()

# Fetch market data
print("[3/7] Fetching market data...")
try:
    ticker = exchange.fetch_ticker('ADA/USDT')
    current_price = ticker['last']
    print(f"      ADA/USDT Price: ${current_price:.4f}")
    print()
except Exception as e:
    print(f"      [ERROR] Failed to fetch data: {e}")
    exit(1)

# Test balance check
print("[4/7] Checking account balance...")
try:
    balance = exchange.fetch_balance()
    usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
    print(f"      USDT Balance: ${usdt_balance:.2f}")

    if usdt_balance < 10:
        print(f"      [WARNING] Low balance (${usdt_balance:.2f})")
        print(f"      Note: Testnet accounts start with virtual funds")
    print()
except Exception as e:
    print(f"      [ERROR] Failed to fetch balance: {e}")
    exit(1)

# Calculate test order size (very small - $10 worth)
test_amount = 10 / current_price  # $10 worth of ADA
print(f"[5/7] Placing TEST BUY order...")
print(f"      Size: {test_amount:.4f} ADA (${10:.2f} value)")

try:
    # Place market buy order
    buy_order = exchange.create_market_buy_order('ADA/USDT', test_amount)
    print(f"      [SUCCESS] Buy order placed!")
    print(f"      Order ID: {buy_order['id']}")
    print(f"      Status: {buy_order['status']}")
    print(f"      Amount: {buy_order.get('amount', 'N/A')} ADA")
    print()

    # Wait a moment
    print("[6/7] Waiting 3 seconds before selling...")
    time.sleep(3)

    # Place market sell order to close
    print("[7/7] Placing TEST SELL order to close position...")
    sell_order = exchange.create_market_sell_order('ADA/USDT', test_amount)
    print(f"      [SUCCESS] Sell order placed!")
    print(f"      Order ID: {sell_order['id']}")
    print(f"      Status: {sell_order['status']}")
    print()

    # Test complete
    print("="*80)
    print("TEST RESULT: SUCCESS")
    print("="*80)
    print()
    print("Your bot is ready for the 4-week test!")
    print()
    print("What was tested:")
    print("  [OK] API connection to Binance")
    print("  [OK] Testnet mode activation")
    print("  [OK] Market data fetching")
    print("  [OK] Balance checking")
    print("  [OK] Market BUY order execution")
    print("  [OK] Market SELL order execution")
    print()
    print("Next steps:")
    print("  1. Start the bot: screen -dmS trading_bot python trading_bot.py")
    print("  2. Begin 4-week paper trading test")
    print("  3. Monitor weekly with: python monitor_performance.py")
    print()

except ccxt.InsufficientFunds as e:
    print(f"      [ERROR] Insufficient funds: {e}")
    print()
    print("="*80)
    print("TEST RESULT: FAILED - Insufficient Testnet Balance")
    print("="*80)
    print()
    print("This is likely because Binance testnet doesn't auto-fund accounts.")
    print()
    print("SOLUTION: Use simulation mode instead")
    print("The bot will track trades internally without actual execution.")
    print("This is actually SAFER for 4-week testing!")
    print()

except ccxt.AuthenticationError as e:
    print(f"      [ERROR] Authentication failed: {e}")
    print()
    print("="*80)
    print("TEST RESULT: FAILED - API Key Issue")
    print("="*80)
    print()
    print("Possible causes:")
    print("  1. Testnet mode requires testnet API keys (from testnet.binance.vision)")
    print("  2. Your current keys are for LIVE Binance, not testnet")
    print()
    print("SOLUTION: I can create a simulation-only version that:")
    print("  - Reads real market data (safe)")
    print("  - Simulates trades internally (no actual orders)")
    print("  - Tracks performance as if trading")
    print("  - Perfect for 4-week testing")
    print()

except ccxt.InvalidOrder as e:
    print(f"      [ERROR] Invalid order: {e}")
    print()
    print("="*80)
    print("TEST RESULT: FAILED - Order Rejected")
    print("="*80)
    print()
    print("Possible causes:")
    print("  1. Order size too small (minimum notional requirements)")
    print("  2. Market unavailable in testnet")
    print("  3. API permissions issue")
    print()

except Exception as e:
    print(f"      [ERROR] Unexpected error: {e}")
    print(f"      Error type: {type(e).__name__}")
    print()
    print("="*80)
    print("TEST RESULT: FAILED")
    print("="*80)
    print()
    print("Full error details:")
    print(str(e))
    print()
    print("This suggests testnet trading may not work with your current setup.")
    print("I recommend switching to simulation mode for the 4-week test.")
    print()
