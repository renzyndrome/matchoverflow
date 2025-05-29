#!/bin/bash

# Fix git permissions for www-data user on Digital Ocean server
echo "Fixing git repository permissions..."

# Navigate to the project directory
cd /var/www/matchoverflow

# Fix ownership of the entire repository
sudo chown -R www-data:www-data .

# Fix permissions for git directory
sudo chown -R www-data:www-data .git

# Set proper permissions
sudo chmod -R 755 .

# Make sure git objects are writable
sudo chmod -R 775 .git/objects

# Now try to pull as www-data user
echo "Pulling latest changes..."
sudo -u www-data git pull origin main

echo "Done! Git permissions should now be fixed." 