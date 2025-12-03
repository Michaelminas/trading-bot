# 4-WEEK PAPER TRADING TEST PLAN

## Overview

**Test Duration**: 28 days (4 weeks)
**Mode**: TESTNET (Binance paper trading)
**Capital**: $10,000 (virtual)
**Strategies**: 3 (ADA RSI, SOL Stochastic, XRP ADX)
**Go/No-Go Decision**: End of Week 4

---

## Weekly Milestones

### Week 1: System Stability (Days 1-7)
**Focus**: Make sure bot runs without errors

**Daily Tasks**:
- Check bot is still running: `ps aux | grep trading_bot.py`
- Review logs for errors: `tail -50 trading_bot.log`
- Run monitoring: `python monitor_performance.py`

**Success Criteria**:
- ✅ Bot runs 24/7 without crashes
- ✅ No API connection errors
- ✅ Logs show regular market checks
- ✅ At least 1-3 trades executed

**Red Flags**:
- ❌ Bot crashes or stops
- ❌ Repeated API errors
- ❌ No trades after 7 days (strategies may be broken)

---

### Week 2: Strategy Validation (Days 8-14)
**Focus**: Do strategies behave as expected?

**Daily Tasks**:
- Run: `python monitor_performance.py`
- Check trade count (should be 5-15 trades by now)
- Review exit reasons (stops, targets, signals)

**Success Criteria**:
- ✅ Win rate >40%
- ✅ Profit factor >1.2
- ✅ Mix of wins and losses (not all losses!)
- ✅ Exit reasons make sense (stops, targets working)

**Red Flags**:
- ❌ Win rate <30% (strategies failing)
- ❌ All trades hitting stop loss (bad entries)
- ❌ Drawdown >-20% (too risky)
- ❌ <5 total trades (not active enough)

---

### Week 3: Performance Assessment (Days 15-21)
**Focus**: Are we making money?

**Weekly Review** (Monday):
- Full performance report: `python monitor_performance.py`
- Calculate ROI: (Total P&L / $10,000) × 100
- Check drawdown trend
- Compare to backtests

**Success Criteria**:
- ✅ Positive P&L (any profit is good)
- ✅ Max drawdown <-15%
- ✅ Profit factor >1.5
- ✅ Performance matches backtest expectations

**Red Flags**:
- ❌ Total P&L negative after 21 days
- ❌ Drawdown >-20%
- ❌ Much worse than backtests (overfitting?)

---

### Week 4: Final Decision (Days 22-28)
**Focus**: Go/No-Go for live trading

**End-of-Test Analysis** (Day 28):
1. Run final report: `python monitor_performance.py`
2. Review all 4 weeks of data
3. Calculate final metrics
4. Make go/no-go decision

**Go-Live Criteria** (Must meet ALL):
- ✅ Total P&L positive
- ✅ Win rate ≥45%
- ✅ Profit factor ≥1.5
- ✅ Max drawdown <-15%
- ✅ No major technical issues
- ✅ At least 20 trades executed
- ✅ Performance within 30% of backtests

**No-Go Criteria** (Any ONE fails test):
- ❌ Total P&L negative
- ❌ Win rate <40%
- ❌ Profit factor <1.2
- ❌ Max drawdown >-20%
- ❌ Frequent crashes/errors
- ❌ <10 trades in 4 weeks

---

## Daily Monitoring Routine

### Quick Check (2 minutes, daily)
```bash
# SSH into VM
ssh mickminas_test@35.235.243.161

# Check bot is running
ps aux | grep trading_bot.py

# Check recent logs (look for errors)
tail -20 trading_bot.log

# Done!
```

### Weekly Deep Dive (15 minutes, Monday)
```bash
# SSH into VM
ssh mickminas_test@35.235.243.161
cd ~/trading-bot
source venv/bin/activate

# Run full performance report
python monitor_performance.py

# Review trades file
cat trades.csv | wc -l  # Count trades

# Check for any crash dumps or error files
ls -lah
```

---

## Key Metrics to Track

### Must Track Daily:
1. **Bot Status**: Running or stopped?
2. **Error Count**: Any exceptions in logs?
3. **Trade Count**: Increasing appropriately?

### Must Track Weekly:
1. **Total P&L**: $ and %
2. **Win Rate**: % wins
3. **Max Drawdown**: Worst equity drop
4. **Profit Factor**: Wins $ / Losses $
5. **Avg Trade**: P&L per trade

### Must Track by End:
1. **Total Return**: Final P&L %
2. **Sharpe Ratio**: Risk-adjusted return
3. **Strategy Breakdown**: Which works best?
4. **Trade Frequency**: Trades per week

---

## Emergency Procedures

### Bot Stopped Running
```bash
# Check if still in screen
screen -ls

# If not found, restart
cd ~/trading-bot
source venv/bin/activate
screen -dmS trading_bot python trading_bot.py

# Verify it started
screen -r trading_bot  # Ctrl+A then D to exit
```

### API Errors
```bash
# Test API connection
python pre_flight_check.py

# If fails, check:
# 1. API keys still valid?
# 2. Binance testnet down?
# 3. Network issues?
```

### Suspicious Performance
**If something looks wrong:**
1. Stop bot immediately: `screen -r trading_bot` then Ctrl+C
2. Run validation: `python pre_flight_check.py`
3. Check if accidentally in LIVE mode: `grep "testnet" trading_bot.py`
4. Review logs: `less trading_bot.log`
5. Ask for help before restarting

---

## End-of-Test Decision Matrix

### STRONG GO (Ready for live trading)
- Total return: >5%
- Win rate: >50%
- Profit factor: >2.0
- Max drawdown: <-10%
- Tech issues: None

### CONDITIONAL GO (Proceed with caution)
- Total return: 0-5%
- Win rate: 45-50%
- Profit factor: 1.5-2.0
- Max drawdown: -10% to -15%
- Tech issues: Minor

### NO GO (Do not go live)
- Total return: <0% (negative)
- Win rate: <45%
- Profit factor: <1.5
- Max drawdown: >-15%
- Tech issues: Frequent crashes

---

## After the 4-Week Test

### If GO Decision:
1. Review and adjust position sizes if needed
2. Deposit funds to Binance spot account
3. Change `testnet: True` → `testnet: False`
4. Start with 50% capital for first week (safety)
5. Monitor daily for first 2 weeks
6. Scale to 100% if performing well

### If NO GO Decision:
1. Analyze what went wrong
2. Consider adjusting strategies
3. Run another 4-week test with changes
4. OR go back to backtesting/optimization

---

## Support Files

- **pre_flight_check.py** - Initial validation
- **monitor_performance.py** - Daily/weekly reports
- **trading_bot.log** - All bot activity
- **trades.csv** - Complete trade history
- **daily_report_YYYYMMDD.txt** - Archived daily reports

---

## Questions to Ask After 4 Weeks

1. **Performance**: Did we beat "buy and hold"?
2. **Consistency**: Are returns stable or volatile?
3. **Drawdowns**: Can I stomach the losses?
4. **Trade Frequency**: Too many or too few trades?
5. **Strategy Balance**: Do all 3 strategies work?
6. **Technical**: Any reliability issues?
7. **Confidence**: Do I trust this enough to risk real money?

If you can confidently answer YES to all 7, you're ready for live trading!

---

## Important Reminders

⚠️ **NEVER skip the 4-week test**
⚠️ **NEVER switch to live mode early**
⚠️ **NEVER ignore red flags**
⚠️ **ALWAYS monitor at least weekly**
⚠️ **ALWAYS check testnet mode before running**

This is YOUR money. Take the full 4 weeks. It's worth it.
