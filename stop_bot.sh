#!/bin/bash
# Stop the Inventory Bot

echo "🛑 Stopping Inventory Bot..."

# Find and kill the process
pkill -f "python.*main.py"

# Wait a moment
sleep 1

# Check if it's still running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Bot still running, forcing kill..."
    pkill -9 -f "python.*main.py"
    sleep 1
fi

# Verify it's stopped
if pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ Failed to stop bot"
    exit 1
else
    echo "✅ Bot stopped successfully"
    exit 0
fi
