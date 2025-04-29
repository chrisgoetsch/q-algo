#!/bin/bash

# Local → EC2 sync
EC2_USER=ubuntu
EC2_IP=3.235.88.213
PEM_PATH=~/Desktop/Q-ALGO-v1/qalgo-key.pem
LOCAL_DIR=~/Desktop/q-algo-v2
REMOTE_DIR=~/Q-ALGO-v2

echo "📡 Syncing local → EC2..."
scp -r -i $PEM_PATH $LOCAL_DIR/* $EC2_USER@$EC2_IP:$REMOTE_DIR/
echo "✅ Sync complete."

