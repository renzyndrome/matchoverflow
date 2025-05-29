#!/bin/bash

# Production Update Script for MatchOverflow
# Run this on your Digital Ocean server to pull and apply latest changes

echo "🚀 Updating MatchOverflow in Production"
echo "======================================="
echo ""

# Navigate to the application directory
cd /var/www/matchoverflow

# Ensure correct permissions
echo "🔒 Ensuring correct permissions..."
sudo chown -R www-data:www-data /var/www/matchoverflow

# Show current status
echo "📊 Current git status:"
sudo -u www-data git status --short

# Stash any local changes (if any)
echo ""
echo "📦 Stashing any local changes..."
sudo -u www-data git stash

# Pull latest changes
echo ""
echo "📥 Pulling latest changes from GitHub..."
sudo -u www-data git pull origin main

# Pop stashed changes (if any)
echo ""
echo "📦 Restoring local changes (if any)..."
sudo -u www-data git stash pop || true

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo ""
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
    sudo chown -R www-data:www-data venv
fi

# Activate virtual environment
echo ""
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Update pip
echo ""
echo "📦 Updating pip..."
pip install --upgrade pip

# Install/update dependencies
echo ""
echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt

# Run any database migrations if needed
# (Currently using SQLite, so no migrations needed)

# Ensure proper permissions after all updates
echo ""
echo "🔒 Setting final permissions..."
sudo chown -R www-data:www-data /var/www/matchoverflow
sudo chmod -R 755 /var/www/matchoverflow

# Restart the service
echo ""
echo "🔄 Restarting MatchOverflow service..."
sudo systemctl restart matchoverflow

# Wait a moment for the service to start
sleep 2

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
echo ""
echo "Next steps:"
echo "1. Check your site at http://159.223.83.99 or https://codewithrenzy.com"
echo "2. Monitor logs: sudo journalctl -u matchoverflow -f"
echo "3. If issues occur, check: sudo systemctl status matchoverflow" 