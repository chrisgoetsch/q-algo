#!/bin/bash

# ---------------------------------
# Q-ALGO Fast Deploy Script
# Author: Q Dev
# ---------------------------------

echo "🔵 Fast Deploy: starting..."

# Check if user provided a commit message
if [ -z "$1" ]
then
  echo "🛑 No commit message provided."
  echo "Usage: ./fast_deploy.sh \"your commit message here\""
  exit 1
fi

# Navigate to q-algo-v2 (just in case)
cd ~/q-algo-v2

# Git operations
git add .
git commit -m "$1"
git push origin main

echo "✅ Fast Deploy: code pushed to GitHub successfully."
