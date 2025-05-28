#!/bin/bash

# MatchOverflow Deployment Script for Digital Ocean
# Domain: codewithrenzy.com
# Server IP: 159.223.83.99

echo "🚀 Starting MatchOverflow deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /var/www/matchoverflow
sudo chown $USER:$USER /var/www/matchoverflow

# Clone or pull latest code
cd /var/www/matchoverflow
if [ -d ".git" ]; then
    echo "📥 Pulling latest code..."
    git pull origin main
else
    echo "📥 Cloning repository..."
    # Update this with your actual GitHub repository URL
    git clone https://github.com/YOUR_USERNAME/matchoverflow.git .
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp env.example .env
    echo "⚠️  Please edit /var/www/matchoverflow/.env with your actual values!"
fi

# Set permissions
echo "🔒 Setting permissions..."
sudo chown -R www-data:www-data /var/www/matchoverflow
sudo chmod -R 755 /var/www/matchoverflow

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/matchoverflow.service > /dev/null <<EOF
[Unit]
Description=MatchOverflow FastAPI app
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/matchoverflow
Environment="PATH=/var/www/matchoverflow/venv/bin"
ExecStart=/var/www/matchoverflow/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/matchoverflow > /dev/null <<EOF
server {
    listen 80;
    server_name codewithrenzy.com www.codewithrenzy.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
echo "🔗 Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/matchoverflow /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Start and enable service
echo "🚀 Starting MatchOverflow service..."
sudo systemctl daemon-reload
sudo systemctl enable matchoverflow
sudo systemctl restart matchoverflow

# Check service status
echo "✅ Checking service status..."
sudo systemctl status matchoverflow --no-pager

# Set up SSL with Let's Encrypt
echo "🔒 Setting up SSL certificate..."
sudo certbot --nginx -d codewithrenzy.com -d www.codewithrenzy.com --non-interactive --agree-tos --email your-email@example.com

echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Edit /var/www/matchoverflow/.env with your actual values"
echo "2. Run 'sudo systemctl restart matchoverflow' after editing .env"
echo "3. Your site should be available at https://codewithrenzy.com"
echo "4. Check logs with: sudo journalctl -u matchoverflow -f"
echo ""
echo "DNS Note: It may take up to 48 hours for DNS changes to propagate fully." 