#!/bin/bash

# Production Update Script for MatchOverflow
# Run this on your Digital Ocean server to pull and apply latest changes

echo "🚀 Updating MatchOverflow in Production"
echo "======================================="
echo ""

# Navigate to the application directory
cd /var/www/matchoverflow

# Show current status
echo "📊 Current git status:"
git status --short

# Pull latest changes
echo ""
echo "📥 Pulling latest changes from GitHub..."
sudo -u www-data git pull origin main

# Activate virtual environment
echo ""
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies if requirements.txt changed
echo ""
echo "📦 Checking for dependency updates..."
pip install -r requirements.txt

# Run any database migrations if needed
# (Currently using SQLite, so no migrations needed)

# Restart the service
echo ""
echo "🔄 Restarting MatchOverflow service..."
sudo systemctl restart matchoverflow

# Check service status
echo ""
echo "✅ Checking service status..."
sudo systemctl status matchoverflow --no-pager

# Show recent logs
echo ""
echo "📋 Recent application logs:"
sudo journalctl -u matchoverflow -n 20 --no-pager

echo ""
echo "✨ Update complete!"
echo ""
echo "Next steps:"
echo "1. Check your site at http://159.223.83.99 or https://codewithrenzy.com"
echo "2. Monitor logs: sudo journalctl -u matchoverflow -f"
echo "3. If issues occur, check: sudo systemctl status matchoverflow" 