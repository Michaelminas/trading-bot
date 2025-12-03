"""
PERFORMANCE MONITORING SCRIPT - 4-WEEK PAPER TRADING TEST

Run this daily to track bot performance and catch issues early.
Usage: python monitor_performance.py
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import os

def load_trades():
    """Load trades from CSV"""
    if os.path.exists('trades.csv'):
        return pd.read_csv('trades.csv')
    return pd.DataFrame()

def load_logs():
    """Parse trading_bot.log for key metrics"""
    if not os.path.exists('trading_bot.log'):
        return None

    with open('trading_bot.log', 'r') as f:
        lines = f.readlines()

    return lines

def calculate_metrics(df):
    """Calculate comprehensive performance metrics"""
    if len(df) == 0:
        return None

    # Convert timestamps
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df['holding_time'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600  # hours

    metrics = {
        'total_trades': len(df),
        'wins': len(df[df['pnl_usd'] > 0]),
        'losses': len(df[df['pnl_usd'] <= 0]),
        'win_rate': len(df[df['pnl_usd'] > 0]) / len(df) * 100,
        'total_pnl': df['pnl_usd'].sum(),
        'avg_win': df[df['pnl_usd'] > 0]['pnl_usd'].mean() if len(df[df['pnl_usd'] > 0]) > 0 else 0,
        'avg_loss': df[df['pnl_usd'] <= 0]['pnl_usd'].mean() if len(df[df['pnl_usd'] <= 0]) > 0 else 0,
        'largest_win': df['pnl_usd'].max(),
        'largest_loss': df['pnl_usd'].min(),
        'avg_holding_time': df['holding_time'].mean(),
        'profit_factor': abs(df[df['pnl_usd'] > 0]['pnl_usd'].sum() / df[df['pnl_usd'] <= 0]['pnl_usd'].sum()) if len(df[df['pnl_usd'] <= 0]) > 0 else float('inf'),
    }

    # Calculate drawdown
    df = df.sort_values('exit_time')
    df['cumulative_pnl'] = df['pnl_usd'].cumsum()
    df['running_max'] = df['cumulative_pnl'].expanding().max()
    df['drawdown'] = df['cumulative_pnl'] - df['running_max']
    metrics['max_drawdown'] = df['drawdown'].min()
    metrics['max_drawdown_pct'] = (metrics['max_drawdown'] / 10000) * 100

    # Strategy breakdown
    strategy_stats = df.groupby('strategy').agg({
        'pnl_usd': ['count', 'sum', lambda x: (x > 0).sum() / len(x) * 100]
    }).round(2)

    return metrics, strategy_stats, df

def check_bot_health():
    """Check if bot is running and healthy"""
    # Check if log has recent activity (within last 5 minutes)
    if not os.path.exists('trading_bot.log'):
        return False, "Log file not found"

    # Get last modified time
    last_modified = datetime.fromtimestamp(os.path.getmtime('trading_bot.log'))
    minutes_ago = (datetime.now() - last_modified).total_seconds() / 60

    if minutes_ago > 5:
        return False, f"Bot inactive for {minutes_ago:.1f} minutes"

    return True, "Bot is active"

def generate_report():
    """Generate daily monitoring report"""
    print("="*80)
    print("PAPER TRADING PERFORMANCE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    # Bot health check
    print("BOT HEALTH CHECK")
    print("-"*80)
    is_healthy, status = check_bot_health()
    if is_healthy:
        print(f"[OK] {status}")
    else:
        print(f"[WARNING] {status}")
    print()

    # Load and analyze trades
    df = load_trades()

    if len(df) == 0:
        print("NO TRADES YET")
        print("-"*80)
        print("The bot is running but hasn't executed any trades yet.")
        print("This is normal if:")
        print("  - Bot just started")
        print("  - Market conditions don't match strategy criteria")
        print("  - Waiting for entry signals")
        print()
        return

    metrics, strategy_stats, df_analyzed = calculate_metrics(df)

    # Overall performance
    print("OVERALL PERFORMANCE")
    print("-"*80)
    print(f"Total Trades:        {metrics['total_trades']}")
    print(f"Wins / Losses:       {metrics['wins']} / {metrics['losses']}")
    print(f"Win Rate:            {metrics['win_rate']:.1f}%")
    print(f"Total P&L:           ${metrics['total_pnl']:+,.2f}")
    print(f"Total Return:        {(metrics['total_pnl']/10000)*100:+.2f}%")
    print(f"Avg Win:             ${metrics['avg_win']:,.2f}")
    print(f"Avg Loss:            ${metrics['avg_loss']:,.2f}")
    print(f"Profit Factor:       {metrics['profit_factor']:.2f}")
    print(f"Max Drawdown:        ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.2f}%)")
    print(f"Avg Hold Time:       {metrics['avg_holding_time']:.1f} hours")
    print()

    # Strategy breakdown
    print("STRATEGY PERFORMANCE")
    print("-"*80)
    for strategy in df['strategy'].unique():
        strat_df = df[df['strategy'] == strategy]
        strat_pnl = strat_df['pnl_usd'].sum()
        strat_trades = len(strat_df)
        strat_wr = (strat_df['pnl_usd'] > 0).sum() / len(strat_df) * 100
        print(f"{strategy:12s} | Trades: {strat_trades:3d} | P&L: ${strat_pnl:+8,.2f} | Win Rate: {strat_wr:5.1f}%")
    print()

    # Exit reason analysis
    print("EXIT REASONS")
    print("-"*80)
    exit_reasons = df['reason'].value_counts()
    for reason, count in exit_reasons.items():
        pct = (count / len(df)) * 100
        reason_pnl = df[df['reason'] == reason]['pnl_usd'].sum()
        print(f"{reason:18s} | Count: {count:3d} ({pct:5.1f}%) | P&L: ${reason_pnl:+,.2f}")
    print()

    # Recent trades (last 5)
    print("RECENT TRADES (Last 5)")
    print("-"*80)
    recent = df.tail(5)[['strategy', 'symbol', 'entry_price', 'exit_price', 'pnl_pct', 'pnl_usd', 'reason', 'exit_time']]
    print(recent.to_string(index=False))
    print()

    # Risk alerts
    print("RISK ALERTS")
    print("-"*80)
    alerts = []

    if metrics['win_rate'] < 40:
        alerts.append(f"[WARNING] Win rate below 40% ({metrics['win_rate']:.1f}%)")

    if metrics['max_drawdown_pct'] < -15:
        alerts.append(f"[WARNING] Drawdown exceeds -15% ({metrics['max_drawdown_pct']:.1f}%)")

    if metrics['profit_factor'] < 1.5:
        alerts.append(f"[WARNING] Profit factor below 1.5 ({metrics['profit_factor']:.2f})")

    if len(alerts) == 0:
        print("[OK] No risk alerts")
    else:
        for alert in alerts:
            print(alert)
    print()

    # Calculate days running
    first_trade = df['entry_time'].min()
    last_trade = df['exit_time'].max()
    days_running = (last_trade - first_trade).total_seconds() / 86400

    print("TESTING PROGRESS")
    print("-"*80)
    print(f"First Trade:         {first_trade}")
    print(f"Last Trade:          {last_trade}")
    print(f"Days Running:        {days_running:.1f} / 28 days")
    print(f"Progress:            {(days_running/28)*100:.1f}%")
    print()

    if days_running < 7:
        print("[INFO] Week 1: Early testing phase - monitor for errors")
    elif days_running < 14:
        print("[INFO] Week 2: Building trade history - watch win rate")
    elif days_running < 21:
        print("[INFO] Week 3: Mid-test - assess if strategies perform as expected")
    else:
        print("[INFO] Week 4: Final week - prepare for go/no-go decision")

    print()
    print("="*80)

    # Save report to file
    report_file = f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(report_file, 'w') as f:
        # Redirect print to file (simplified - just save key metrics)
        f.write(f"Daily Report - {datetime.now()}\n")
        f.write(f"Total Trades: {metrics['total_trades']}\n")
        f.write(f"Win Rate: {metrics['win_rate']:.1f}%\n")
        f.write(f"Total P&L: ${metrics['total_pnl']:,.2f}\n")
        f.write(f"Days Running: {days_running:.1f}/28\n")

    print(f"[OK] Report saved to {report_file}")

if __name__ == "__main__":
    generate_report()
