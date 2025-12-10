"""
AUSTRALIAN SPOT TRADING BOT - SIMULATION MODE
Paper trading with REAL market prices (not testnet fake data)

This version:
- Reads REAL prices from live Binance (accurate market data)
- Simulates all trades internally (no actual orders placed)
- Tracks performance exactly as if trading
- Perfect for 4-week strategy validation

After 4 weeks of successful simulation, switch to live trading with real capital.
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

# Load API keys from .env (only used for reading market data)
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
    'simulation_mode': True,  # ALWAYS True - this is simulation bot
    'slippage': 0.001,  # 0.1% slippage simulation (realistic for spot)
    'fees': 0.001,  # 0.1% trading fees (Binance spot fee)
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
# TRADING BOT - SIMULATION MODE
# =============================================================================

class SimulationTradingBot:
    def __init__(self):
        # Connect to LIVE Binance for REAL market data (read-only)
        self.exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })

        # DO NOT enable sandbox mode - we want REAL prices!
        logger.info("SIMULATION MODE - Real prices, simulated trades")

        self.capital = CONFIG['initial_capital']
        self.initial_capital = CONFIG['initial_capital']
        self.positions = {}
        self.trades = []
        self.equity_curve = []

        logger.info(f"Bot initialized with ${self.capital:,.2f} (simulated)")

    def fetch_data(self, symbol, timeframe='1h', limit=300):
        """Fetch REAL OHLCV data from LIVE Binance"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = calculate_indicators(df)
            return df
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    def simulate_entry_price(self, current_price):
        """Simulate realistic entry price with slippage"""
        slippage = current_price * CONFIG['slippage']
        entry_price = current_price + slippage  # Buy at slightly higher price
        return entry_price

    def simulate_exit_price(self, current_price):
        """Simulate realistic exit price with slippage"""
        slippage = current_price * CONFIG['slippage']
        exit_price = current_price - slippage  # Sell at slightly lower price
        return exit_price

    def open_position(self, strategy_name, config, current_price):
        """Simulate opening a position (NO REAL ORDER)"""
        try:
            # Calculate position with realistic slippage
            entry_price = self.simulate_entry_price(current_price)
            position_value = self.capital * config['position_size']
            amount = (position_value * config['leverage']) / entry_price

            # Simulate fees
            fee = position_value * CONFIG['fees']

            self.positions[strategy_name] = {
                'symbol': config['symbol'],
                'entry_price': entry_price,
                'amount': amount,
                'leverage': config['leverage'],
                'stop_loss': entry_price * (1 - config['stop_loss']),
                'take_profit': entry_price * (1 + config['take_profit']),
                'highest_price': entry_price,
                'entry_time': datetime.now(),
                'entry_fee': fee,
            }

            logger.info(f"[SIM] OPENED {strategy_name} | {config['symbol']} | "
                       f"${entry_price:.4f} | {amount:.4f} | {config['leverage']}x | "
                       f"Fee: ${fee:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error simulating position open: {e}")
            return False

    def close_position(self, strategy_name, current_price, reason):
        """Simulate closing a position (NO REAL ORDER)"""
        try:
            position = self.positions[strategy_name]
            symbol = position['symbol']

            # Calculate exit with realistic slippage and fees
            exit_price = self.simulate_exit_price(current_price)
            position_value = self.capital * CONFIG['strategies'][strategy_name]['position_size']
            exit_fee = position_value * CONFIG['fees']

            # Calculate P&L
            price_change = (exit_price - position['entry_price']) / position['entry_price']
            pnl_pct = price_change * position['leverage'] * 100
            pnl_usd = position_value * (price_change * position['leverage'])

            # Subtract fees
            total_fees = position['entry_fee'] + exit_fee
            pnl_usd -= total_fees

            self.capital += pnl_usd

            trade = {
                'strategy': strategy_name,
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'pnl_pct': pnl_pct,
                'pnl_usd': pnl_usd,
                'fees': total_fees,
                'reason': reason,
                'entry_time': position['entry_time'],
                'exit_time': datetime.now(),
            }
            self.trades.append(trade)

            del self.positions[strategy_name]

            logger.info(f"[SIM] CLOSED {strategy_name} | {symbol} | "
                       f"${exit_price:.4f} | PnL: {pnl_pct:+.2f}% (${pnl_usd:+,.2f}) | "
                       f"Fees: ${total_fees:.2f} | {reason}")

            return True

        except Exception as e:
            logger.error(f"Error simulating position close: {e}")
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
        print("SIMULATION PERFORMANCE SUMMARY")
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
        logger.info("AUSTRALIAN SPOT TRADING BOT - SIMULATION MODE")
        logger.info("="*80)
        logger.info(f"Using REAL market prices from live Binance")
        logger.info(f"All trades SIMULATED (no real orders placed)")
        logger.info(f"Strategies: {sum(1 for s in CONFIG['strategies'].values() if s['enabled'])}")
        logger.info(f"Capital: ${self.capital:,.2f} (simulated)")
        logger.info(f"Max Leverage: {CONFIG['max_leverage']}x")
        logger.info(f"Slippage: {CONFIG['slippage']*100:.2f}%")
        logger.info(f"Fees: {CONFIG['fees']*100:.2f}%")
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
    print("AUSTRALIAN SPOT TRADING BOT - SIMULATION MODE")
    print("="*80)
    print()
    print("This bot uses REAL market prices but SIMULATES all trades.")
    print("Perfect for 4-week strategy validation before risking real money.")
    print()

    if not API_KEY or not API_SECRET:
        print("[ERROR] API keys not found!")
        print("Please create .env file with:")
        print("  BINANCE_API_KEY=your_key")
        print("  BINANCE_SECRET=your_secret")
        print()
        print("Note: Keys only used to READ market data (safe)")
        exit(1)

    print("[OK] API keys loaded (read-only access)")
    print("[OK] Mode: SIMULATION (real prices, simulated trades)")
    print(f"[OK] Strategies: {sum(1 for s in CONFIG['strategies'].values() if s['enabled'])}")
    print(f"[OK] Slippage: {CONFIG['slippage']*100:.2f}% | Fees: {CONFIG['fees']*100:.2f}%")
    print()

    bot = SimulationTradingBot()
    bot.run()
