#!/bin/bash

# ---------------------------------
# Q-ALGO Restore Script
# Author: Q Dev
# ---------------------------------

# Configuration
REPO_URL="https://github.com/chrisgoetsch/Q-algo.git"
LOCAL_DIR="$HOME/Q-ALGO-v2"

# 1. Check if Git is installed
if ! command -v git &> /dev/null
then
    echo "Git could not be found. Installing git..."
    sudo apt-get update
    sudo apt-get install -y git
fi

# 2. Clone or Pull Repository
if [ -d "$LOCAL_DIR/.git" ]; then
    echo "Existing repo found. Pulling latest updates..."
    cd "$LOCAL_DIR"
    git pull origin main
else
    echo "Cloning fresh Q-ALGO repo..."
    git clone "$REPO_URL" "$LOCAL_DIR"
fi

# 3. Recreate logs and backups folders if missing
mkdir -p "$LOCAL_DIR/logs"
mkdir -p "$LOCAL_DIR/backups"

# 4. Confirm critical files restored
echo "Checking important files..."
ls -l "$LOCAL_DIR/logs"
ls -l "$LOCAL_DIR/backups"
ls -l "$LOCAL_DIR/core"
ls -l "$LOCAL_DIR/mesh"

# 5. Restore cron jobs (optional, uncomment if you want)
# echo "Restoring nightly cron jobs..."
# (crontab -l ; echo "55 23 * * * cd $LOCAL_DIR && /usr/bin/python3 memory_compression.py >> logs/memory_compression.log 2>&1") | crontab -
# (crontab -l ; echo "5 0 * * * mkdir -p $LOCAL_DIR/backups/\$(date +\%Y-\%m-\%d) && cp -r $LOCAL_DIR/logs/* $LOCAL_DIR/backups/\$(date +\%Y-\%m-\%d)/") | crontab -
# (crontab -l ; echo "10 0 * * * cd $LOCAL_DIR && git add logs/ backups/ && git commit -m \"Nightly memory backup\" && git push origin main") | crontab -

# 6. Finish
echo "✅ Q-ALGO system files restored successfully."
echo "⚡ Please manually check your .env file for secrets (tokens, API keys)."
