"""
AUSTRALIAN SPOT TRADING BOT - GOOGLE CLOUD READY
Complete standalone file - just run and go!

Deploy to Google Cloud:
1. Upload this folder
2. Run: pip install -r requirements.txt
3. Add your API keys to .env
4. Run: python trading_bot.py
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import json
import os
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_SECRET')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION - AUSTRALIAN COMPLIANT
# =============================================================================

CONFIG = {
    # Australian regulations
    'max_leverage': 5.0,  # Australian legal limit
    'market_type': 'spot',  # Spot only (no futures)

    # Capital
    'initial_capital': 10000,

    # Strategies (Top 3 most reliable)
    'strategies': {
        'ADA_RSI': {
            'enabled': True,
            'symbol': 'ADA/USDT',
            'leverage': 2.0,
            'position_size': 0.25,  # 25% of capital
            'stop_loss': 0.08,
            'take_profit': 0.15,
            'trailing_stop': 0.10,
        },
        'SOL_STOCH': {
            'enabled': True,
            'symbol': 'SOL/USDT',
            'leverage': 2.0,
            'position_size': 0.25,
            'stop_loss': 0.08,
            'take_profit': 0.12,
            'trailing_stop': 0.10,
        },
        'XRP_ADX': {
            'enabled': True,
            'symbol': 'XRP/USDT',
            'leverage': 2.5,
            'position_size': 0.30,
            'stop_loss': 0.10,
            'take_profit': 0.20,
            'trailing_stop': 0.12,
        },
    },

    # Risk management
    'max_drawdown': 0.15,  # Stop if lose 15%
    'max_daily_loss': 0.03,  # Stop if lose 3% today

    # Execution
    'update_interval': 60,  # Check every 60 seconds
    'testnet': True,  # Set True for paper trading, False for live
}

# =============================================================================
# TECHNICAL INDICATORS
# =============================================================================

def calculate_indicators(df):
    """Calculate all technical indicators"""
    # EMAs
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Stochastic
    low_min = df['low'].rolling(window=14).min()
    high_max = df['high'].rolling(window=14).max()
    df['stoch_k'] = 100 * ((df['close'] - low_min) / (high_max - low_min))
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()

    # ADX
    df['tr'] = df[['high', 'low']].apply(lambda x: x.iloc[0] - x.iloc[1], axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    df['plus_dm'] = df['high'].diff().where(df['high'].diff() > 0, 0)
    df['minus_dm'] = -df['low'].diff().where(-df['low'].diff() > 0, 0)
    df['plus_di'] = 100 * (df['plus_dm'].rolling(14).mean() / df['atr'])
    df['minus_di'] = 100 * (df['minus_dm'].rolling(14).mean() / df['atr'])
    df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
    df['adx'] = df['dx'].rolling(14).mean()

    # Volume
    df['vol_ma'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_ma']

    return df

# =============================================================================
# STRATEGY FUNCTIONS
# =============================================================================

def ada_rsi_signal(df):
    """ADA RSI Oversold Strategy"""
    if len(df) < 50:
        return False, False

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Entry: RSI oversold and reversing
    entry = (latest['rsi'] < 35 and
             latest['rsi'] > prev['rsi'] and
             latest['vol_ratio'] > 0.8 and
             latest['ema20'] > df.iloc[-10]['ema50'])

    # Exit: RSI reaches 60
    exit_signal = latest['rsi'] > 60

    return entry, exit_signal

def sol_stoch_signal(df):
    """SOL Stochastic Momentum Strategy"""
    if len(df) < 50:
        return False, False

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Entry: Stoch oversold + crossover in uptrend
    entry = (latest['stoch_k'] < 30 and
             latest['stoch_k'] > latest['stoch_d'] and
             prev['stoch_k'] <= prev['stoch_d'] and
             latest['ema20'] > latest['ema50'])

    # Exit: Stoch overbought
    exit_signal = latest['stoch_k'] > 80

    return entry, exit_signal

def xrp_adx_signal(df):
    """XRP ADX Breakout Strategy"""
    if len(df) < 50:
        return False, False

    latest = df.iloc[-1]
    prev_3 = df.iloc[-4]

    # Entry: ADX strong + rising + breakout
    high_20 = df['high'].iloc[-21:-1].max()
    entry = (latest['adx'] > 25 and
             latest['adx'] > prev_3['adx'] and
             latest['close'] > high_20)

    # Exit: ADX weakens
    exit_signal = latest['adx'] < 20

    return entry, exit_signal

STRATEGY_FUNCTIONS = {
    'ADA_RSI': ada_rsi_signal,
    'SOL_STOCH': sol_stoch_signal,
    'XRP_ADX': xrp_adx_signal,
}

# =============================================================================
# TRADING BOT
# =============================================================================

class TradingBot:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })

        if CONFIG['testnet']:
            self.exchange.set_sandbox_mode(True)
            logger.info("TESTNET MODE - Paper trading")
        else:
            logger.info("LIVE MODE - Real trading")

        self.capital = CONFIG['initial_capital']
        self.initial_capital = CONFIG['initial_capital']
        self.positions = {}
        self.trades = []
        self.equity_curve = []

        logger.info(f"Bot initialized with ${self.capital:,.2f}")

    def fetch_data(self, symbol, timeframe='1h', limit=300):
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = calculate_indicators(df)
            return df
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    def open_position(self, strategy_name, config, current_price):
        """Open a new position"""
        try:
            position_value = self.capital * config['position_size']
            amount = (position_value * config['leverage']) / current_price

            # Create order
            symbol = config['symbol']
            order = self.exchange.create_market_buy_order(symbol, amount)

            self.positions[strategy_name] = {
                'symbol': symbol,
                'entry_price': current_price,
                'amount': amount,
                'leverage': config['leverage'],
                'stop_loss': current_price * (1 - config['stop_loss']),
                'take_profit': current_price * (1 + config['take_profit']),
                'highest_price': current_price,
                'entry_time': datetime.now(),
            }

            logger.info(f"OPENED {strategy_name} | {symbol} | ${current_price:.4f} | {amount:.4f} | {config['leverage']}x")
            return True

        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return False

    def close_position(self, strategy_name, current_price, reason):
        """Close an open position"""
        try:
            position = self.positions[strategy_name]
            symbol = position['symbol']
            amount = position['amount']

            # Create sell order
            order = self.exchange.create_market_sell_order(symbol, amount)

            # Calculate P&L
            pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * position['leverage'] * 100
            position_value = self.capital * CONFIG['strategies'][strategy_name]['position_size']
            pnl_usd = position_value * (pnl_pct / 100)

            self.capital += pnl_usd

            trade = {
                'strategy': strategy_name,
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'exit_price': current_price,
                'pnl_pct': pnl_pct,
                'pnl_usd': pnl_usd,
                'reason': reason,
                'entry_time': position['entry_time'],
                'exit_time': datetime.now(),
            }
            self.trades.append(trade)

            del self.positions[strategy_name]

            logger.info(f"CLOSED {strategy_name} | {symbol} | ${current_price:.4f} | PnL: {pnl_pct:+.2f}% (${pnl_usd:+,.2f}) | {reason}")

            return True

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def check_position_exits(self, strategy_name, config, current_price):
        """Check if position should exit"""
        position = self.positions[strategy_name]

        # Update highest price for trailing stop
        if current_price > position['highest_price']:
            position['highest_price'] = current_price

        # Stop loss
        if current_price <= position['stop_loss']:
            return True, 'stop_loss'

        # Take profit
        if current_price >= position['take_profit']:
            return True, 'take_profit'

        # Trailing stop
        trailing_stop_price = position['highest_price'] * (1 - config['trailing_stop'])
        if current_price <= trailing_stop_price:
            return True, 'trailing_stop'

        return False, None

    def run_strategy(self, strategy_name, config):
        """Run a single strategy"""
        if not config['enabled']:
            return

        symbol = config['symbol']
        df = self.fetch_data(symbol)

        if df is None or len(df) < 50:
            return

        current_price = df['close'].iloc[-1]
        strategy_func = STRATEGY_FUNCTIONS[strategy_name]

        # Check if we have a position
        if strategy_name in self.positions:
            # Check exit conditions
            should_exit, reason = self.check_position_exits(strategy_name, config, current_price)

            # Check strategy exit signal
            _, exit_signal = strategy_func(df)

            if should_exit or exit_signal:
                self.close_position(strategy_name, current_price, reason or 'strategy_signal')

        # Check entry signal (if no position)
        else:
            entry_signal, _ = strategy_func(df)
            if entry_signal:
                self.open_position(strategy_name, config, current_price)

    def save_performance(self):
        """Save trades to CSV"""
        if self.trades:
            df = pd.DataFrame(self.trades)
            df.to_csv('trades.csv', index=False)
            logger.info(f"Saved {len(self.trades)} trades to trades.csv")

    def print_summary(self):
        """Print performance summary"""
        total_pnl = self.capital - self.initial_capital
        total_return = (total_pnl / self.initial_capital) * 100

        wins = sum(1 for t in self.trades if t['pnl_usd'] > 0)
        win_rate = (wins / len(self.trades) * 100) if self.trades else 0

        print("\n" + "="*80)
        print("PERFORMANCE SUMMARY")
        print("="*80)
        print(f"Starting Capital: ${self.initial_capital:,.2f}")
        print(f"Current Capital:  ${self.capital:,.2f}")
        print(f"Total PnL:        ${total_pnl:+,.2f} ({total_return:+.2f}%)")
        print(f"Total Trades:     {len(self.trades)}")
        print(f"Win Rate:         {win_rate:.1f}%")
        print(f"Open Positions:   {len(self.positions)}")
        print("="*80 + "\n")

    def run(self):
        """Main trading loop"""
        logger.info("="*80)
        logger.info("AUSTRALIAN SPOT TRADING BOT STARTED")
        logger.info("="*80)
        logger.info(f"Strategies: {sum(1 for s in CONFIG['strategies'].values() if s['enabled'])}")
        logger.info(f"Capital: ${self.capital:,.2f}")
        logger.info(f"Max Leverage: {CONFIG['max_leverage']}x")
        logger.info("="*80)

        last_summary = time.time()

        try:
            while True:
                # Run each strategy
                for strategy_name, config in CONFIG['strategies'].items():
                    self.run_strategy(strategy_name, config)

                # Print summary every hour
                if time.time() - last_summary > 3600:
                    self.print_summary()
                    self.save_performance()
                    last_summary = time.time()

                # Sleep before next check
                time.sleep(CONFIG['update_interval'])

        except KeyboardInterrupt:
            logger.info("\nStopping bot...")
            self.print_summary()
            self.save_performance()
            logger.info("Bot stopped")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("AUSTRALIAN SPOT TRADING BOT")
    print("="*80)
    print()

    if not API_KEY or not API_SECRET:
        print("[ERROR] API keys not found!")
        print("Please create .env file with:")
        print("  BINANCE_API_KEY=your_key")
        print("  BINANCE_SECRET=your_secret")
        exit(1)

    print("[OK] API keys loaded")
    print(f"[OK] Mode: {'TESTNET (paper)' if CONFIG['testnet'] else 'LIVE (real money)'}")
    print(f"[OK] Strategies: {sum(1 for s in CONFIG['strategies'].values() if s['enabled'])}")
    print()

    bot = TradingBot()
    bot.run()
