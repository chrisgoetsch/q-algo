#!/bin/bash

cd ~/Q-ALGO-v2

echo "🔁 Staging all changes..."
git add .

echo "📝 Enter commit message:"
read COMMIT_MSG

git commit -m "$COMMIT_MSG"
git push origin main
echo "🚀 Push to GitHub complete."

