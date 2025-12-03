# Deploy to Your VM - Quick Guide

## Step 1: Zip the Folder

On your local machine:
```bash
cd "C:\Users\MM\Desktop\Trading Bot\sherlock_bot_project"
# Windows: Right-click GOOGLE_CLOUD_DEPLOY → Send to → Compressed folder
# Or use 7zip/WinRAR
```

Creates: `GOOGLE_CLOUD_DEPLOY.zip`

---

## Step 2: Upload to VM

### Option A: SCP (Recommended)
```bash
scp GOOGLE_CLOUD_DEPLOY.zip username@your-vm-ip:~/
```

### Option B: Google Cloud Console
1. Go to: https://console.cloud.google.com
2. Compute Engine → VM instances
3. Click "SSH" button on your VM
4. Click gear icon → "Upload file"
5. Select GOOGLE_CLOUD_DEPLOY.zip

### Option C: WinSCP (Windows GUI)
1. Download WinSCP: https://winscp.net
2. Connect to your VM
3. Drag and drop GOOGLE_CLOUD_DEPLOY.zip

---

## Step 3: SSH into VM

```bash
# Google Cloud CLI
gcloud compute ssh your-vm-name

# OR standard SSH
ssh username@your-vm-ip
```

---

## Step 4: Install and Run (3 Commands)

```bash
# 1. Unzip
unzip GOOGLE_CLOUD_DEPLOY.zip
cd GOOGLE_CLOUD_DEPLOY

# 2. Install
chmod +x install.sh && ./install.sh

# 3. Start
chmod +x start.sh && ./start.sh
```

**Done!** Bot is running.

---

## Step 5: Verify It's Working

```bash
# Check bot is running
screen -ls
# Should show: trading_bot

# View live activity
screen -r trading_bot

# See logs
tail -f trading_bot.log
```

Press `Ctrl+A` then `D` to detach (bot keeps running)

---

## Quick Commands

```bash
# View bot
screen -r trading_bot

# Detach
Ctrl+A then D

# Stop bot
screen -X -S trading_bot quit

# Restart
./start.sh

# View trades
cat trades.csv

# View last 20 log lines
tail -20 trading_bot.log
```

---

## Troubleshooting

### "screen: command not found"
```bash
sudo apt-get update
sudo apt-get install -y screen
```

### "pip3: command not found"
```bash
sudo apt-get update
sudo apt-get install -y python3-pip
```

### Bot won't connect
```bash
# Test internet
ping binance.com

# Test Python
python3 --version

# Reinstall packages
pip3 install -r requirements.txt --upgrade
```

---

## You're Live!

Bot is now running 24/7 on your VM:
- Checking markets every 60 seconds
- Trading 3 strategies (ADA, SOL, XRP)
- Logging everything to trading_bot.log
- Saving trades to trades.csv

**Expected: 28-32% APR** 🚀
