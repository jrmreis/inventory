#!/bin/bash
# Restart the Inventory Bot

echo "🔄 Restarting Inventory Bot..."

# Stop the bot first
echo "Stopping bot..."
pkill -f "python.*main.py"
sleep 2

# Verify it's stopped
if pgrep -f "python.*main.py" > /dev/null; then
    echo "Force killing..."
    pkill -9 -f "python.*main.py"
    sleep 1
fi

# Start the bot
echo "Starting bot..."
cd "$(dirname "$0")"
source venv/bin/activate
nohup python main.py > bot.log 2>&1 &
NEW_PID=$!

sleep 2

# Check if it started
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ Bot restarted successfully with PID: $NEW_PID"
    tail -10 bot.log
else
    echo "❌ Failed to start bot"
    echo "Check bot.log for errors:"
    tail -20 bot.log
    exit 1
fi
