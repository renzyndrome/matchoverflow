#!/bin/bash

# SSL Setup Script for MatchOverflow
# Run this after DNS has propagated

echo "🔒 SSL Setup for MatchOverflow"
echo "=============================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run with sudo: sudo ./setup-ssl.sh"
    exit 1
fi

# Function to check DNS
check_dns() {
    local domain=$1
    local ip=$(dig +short $domain | tail -n1)
    
    if [ -z "$ip" ]; then
        echo "❌ $domain - NOT RESOLVING"
        return 1
    elif [ "$ip" = "159.223.83.99" ]; then
        echo "✅ $domain → $ip (Correct!)"
        return 0
    else
        echo "❌ $domain → $ip (Wrong IP! Should be 159.223.83.99)"
        return 1
    fi
}

# Check DNS resolution
echo "📡 Checking DNS resolution..."
echo ""

dns_ok=true
check_dns "codewithrenzy.com" || dns_ok=false
check_dns "www.codewithrenzy.com" || dns_ok=false

echo ""

if [ "$dns_ok" = false ]; then
    echo "❌ DNS is not properly configured yet!"
    echo ""
    echo "Please ensure both domains point to 159.223.83.99"
    echo "DNS changes can take 15 minutes to 48 hours to propagate."
    echo ""
    echo "You can check propagation status at:"
    echo "  https://www.whatsmydns.net/#A/codewithrenzy.com"
    echo "  https://www.whatsmydns.net/#A/www.codewithrenzy.com"
    exit 1
fi

echo "✅ DNS is properly configured!"
echo ""

# Ask for email
read -p "Enter your email for Let's Encrypt notifications: " email
if [ -z "$email" ]; then
    echo "❌ Email is required for Let's Encrypt"
    exit 1
fi

# Try to get certificate
echo ""
echo "🔒 Requesting SSL certificate..."
echo ""

# First try both domains
certbot --nginx \
    -d codewithrenzy.com \
    -d www.codewithrenzy.com \
    --non-interactive \
    --agree-tos \
    --email "$email" \
    --redirect

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate installed successfully!"
    echo ""
    echo "Your site is now available at:"
    echo "  https://codewithrenzy.com"
    echo "  https://www.codewithrenzy.com"
    echo ""
    echo "Certificate will auto-renew. You can test renewal with:"
    echo "  sudo certbot renew --dry-run"
else
    echo ""
    echo "❌ SSL setup failed!"
    echo ""
    echo "Common issues:"
    echo "1. DNS not fully propagated (wait longer)"
    echo "2. Firewall blocking port 80/443"
    echo "3. Nginx configuration issues"
    echo ""
    echo "You can try getting certificate for just the main domain:"
    echo "  sudo certbot --nginx -d codewithrenzy.com"
    echo ""
    echo "Check Nginx error logs:"
    echo "  sudo tail -f /var/log/nginx/error.log"
fi 