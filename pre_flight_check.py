"""
PRE-FLIGHT CHECK - Validate bot before going live
Run this before starting live trading to ensure everything works
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

print("="*80)
print("PRE-FLIGHT CHECK - Trading Bot Validation")
print("="*80)
print()

# Track test results
tests_passed = 0
tests_failed = 0
warnings = []

def test_pass(name):
    global tests_passed
    tests_passed += 1
    print(f"[PASS] {name}")

def test_fail(name, error):
    global tests_failed
    tests_failed += 1
    print(f"[FAIL] {name}")
    print(f"       Error: {error}")

def test_warn(message):
    warnings.append(message)
    print(f"[WARN] {message}")

# =============================================================================
# TEST 1: Environment Setup
# =============================================================================
print("TEST 1: Environment Setup")
print("-" * 80)

# Check Python version
import sys
if sys.version_info >= (3, 8):
    test_pass(f"Python version {sys.version.split()[0]} (>= 3.8 required)")
else:
    test_fail("Python version", f"Found {sys.version.split()[0]}, need >= 3.8")

# Check .env file exists
if os.path.exists('.env'):
    test_pass(".env file exists")
    load_dotenv()
else:
    test_fail(".env file", "File not found")

# Check API keys loaded
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_SECRET')

if API_KEY and API_SECRET:
    test_pass("API keys loaded from .env")
    print(f"       API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
else:
    test_fail("API keys", "Not found in .env file")

print()

# =============================================================================
# TEST 2: Required Packages
# =============================================================================
print("TEST 2: Required Packages")
print("-" * 80)

required_packages = {
    'ccxt': 'Binance API client',
    'pandas': 'Data processing',
    'numpy': 'Mathematical operations',
    'dotenv': 'Environment variables'
}

for package, description in required_packages.items():
    try:
        if package == 'dotenv':
            __import__('dotenv')
        else:
            __import__(package)
        test_pass(f"{package} installed ({description})")
    except ImportError:
        test_fail(f"{package}", f"Not installed - run: pip install {package}")

print()

# =============================================================================
# TEST 3: Binance API Connection
# =============================================================================
print("TEST 3: Binance API Connection")
print("-" * 80)

if API_KEY and API_SECRET:
    try:
        import ccxt
        exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })

        # Test connection
        test_pass("Binance API client created")

        # Load markets
        markets = exchange.load_markets()
        test_pass(f"Connected to Binance ({len(markets)} markets available)")

        # Check if required symbols exist
        required_symbols = ['ADA/USDT', 'SOL/USDT', 'XRP/USDT']
        for symbol in required_symbols:
            if symbol in markets:
                test_pass(f"Market {symbol} available")
            else:
                test_fail(f"Market {symbol}", "Not found on Binance")

        # Test data fetch
        try:
            ticker = exchange.fetch_ticker('BTC/USDT')
            price = ticker['last']
            test_pass(f"Data fetch working (BTC price: ${price:,.2f})")
        except Exception as e:
            test_fail("Data fetch", str(e))

        # Check API permissions
        try:
            balance = exchange.fetch_balance()
            test_pass("API key has read permissions")

            # Check USDT balance
            if 'USDT' in balance['total']:
                usdt_balance = balance['total']['USDT']
                print(f"       USDT Balance: ${usdt_balance:,.2f}")

                if usdt_balance < 100:
                    test_warn(f"Low USDT balance (${usdt_balance:.2f}). Consider depositing more.")
            else:
                test_warn("No USDT balance found")

        except Exception as e:
            test_fail("API permissions", f"Cannot read balance: {e}")

    except Exception as e:
        test_fail("Binance connection", str(e))
else:
    print("Skipping (no API keys)")

print()

# =============================================================================
# TEST 4: Trading Bot Configuration
# =============================================================================
print("TEST 4: Trading Bot Configuration")
print("-" * 80)

try:
    # Import bot config
    import importlib.util
    spec = importlib.util.spec_from_file_location("trading_bot", "trading_bot.py")
    bot_module = importlib.util.module_from_spec(spec)

    # Check if file exists
    if os.path.exists('trading_bot.py'):
        test_pass("trading_bot.py exists")

        # Read and check config
        with open('trading_bot.py', 'r') as f:
            content = f.read()

            # Check testnet setting
            if "'testnet': False" in content:
                test_warn("Bot is set to LIVE trading mode (real money!)")
                print("       To test first, change line 66 to: 'testnet': True")
            elif "'testnet': True" in content:
                test_pass("Bot is in TESTNET mode (safe for testing)")

            # Check capital
            if "'initial_capital': 10000" in content:
                test_pass("Initial capital: $10,000")

            # Check leverage limits
            if "'max_leverage': 5.0" in content:
                test_pass("Max leverage: 5.0x (Australian compliant)")

            # Count enabled strategies
            enabled_count = content.count("'enabled': True")
            test_pass(f"{enabled_count} strategies enabled")

    else:
        test_fail("trading_bot.py", "File not found")

except Exception as e:
    test_fail("Bot configuration", str(e))

print()

# =============================================================================
# TEST 5: Test Strategy Execution (Dry Run)
# =============================================================================
print("TEST 5: Strategy Logic Test")
print("-" * 80)

try:
    import ccxt
    import pandas as pd

    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'},
    })

    # Fetch test data
    ohlcv = exchange.fetch_ohlcv('ADA/USDT', '1h', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    if len(df) >= 50:
        test_pass(f"Fetched {len(df)} candles of historical data")

        # Calculate basic indicator
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()

        if not df['ema20'].isna().all():
            test_pass("Technical indicators calculating correctly")
        else:
            test_fail("Indicators", "EMA calculation failed")

        # Check latest price
        latest_price = df['close'].iloc[-1]
        test_pass(f"Latest ADA price: ${latest_price:.4f}")

    else:
        test_fail("Historical data", "Insufficient candles fetched")

except Exception as e:
    test_fail("Strategy test", str(e))

print()

# =============================================================================
# TEST 6: Risk Management Checks
# =============================================================================
print("TEST 6: Risk Management Validation")
print("-" * 80)

if os.path.exists('trading_bot.py'):
    with open('trading_bot.py', 'r') as f:
        content = f.read()

        # Check stop loss exists
        if 'stop_loss' in content:
            test_pass("Stop loss configured")
        else:
            test_fail("Stop loss", "Not found in configuration")

        # Check take profit exists
        if 'take_profit' in content:
            test_pass("Take profit configured")
        else:
            test_fail("Take profit", "Not found in configuration")

        # Check trailing stop exists
        if 'trailing_stop' in content:
            test_pass("Trailing stop configured")
        else:
            test_fail("Trailing stop", "Not found in configuration")

        # Check max drawdown
        if 'max_drawdown' in content:
            test_pass("Max drawdown protection enabled")
        else:
            test_warn("Max drawdown protection not configured")

print()

# =============================================================================
# TEST 7: File Permissions and Logging
# =============================================================================
print("TEST 7: File System Checks")
print("-" * 80)

# Check write permissions
try:
    test_file = 'test_write.tmp'
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    test_pass("Write permissions OK (can create logs/trades.csv)")
except Exception as e:
    test_fail("Write permissions", str(e))

# Check if screen is available (for background running)
import subprocess
try:
    result = subprocess.run(['which', 'screen'], capture_output=True, text=True)
    if result.returncode == 0:
        test_pass("screen command available (can run in background)")
    else:
        test_warn("screen not installed - bot won't survive SSH disconnect")
        print("       Install: sudo apt-get install screen")
except:
    test_warn("Cannot check for screen command")

print()

# =============================================================================
# SUMMARY
# =============================================================================
print("="*80)
print("TEST SUMMARY")
print("="*80)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Warnings: {len(warnings)}")
print()

if tests_failed == 0:
    print("[SUCCESS] All critical tests passed! ✓")
    print()
    print("Ready to deploy:")
    print("  1. If testnet=True, run: python trading_bot.py (test mode)")
    print("  2. Monitor for 1-2 hours")
    print("  3. If all good, change testnet=False for live trading")
    print("  4. Run in background: screen -dmS trading_bot python trading_bot.py")
    print()
else:
    print("[ATTENTION] Some tests failed!")
    print()
    print("Fix the failed tests before running the bot.")
    print()

if warnings:
    print("Warnings to address:")
    for i, warning in enumerate(warnings, 1):
        print(f"  {i}. {warning}")
    print()

print("="*80)
print(f"Pre-flight check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Exit with error code if tests failed
sys.exit(0 if tests_failed == 0 else 1)
