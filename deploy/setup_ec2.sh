#!/usr/bin/env bash
# ==============================================================================
# Masar Umrah CRM - AWS EC2 Turnkey Setup Script
# Domain: umrahdesk.masarumrah.com
# Database: SQLite (db.sqlite3 on this EC2 instance)
# OS: Ubuntu 22.04 / 24.04 LTS on AWS EC2
# ==============================================================================

set -e

echo "=== 1. Updating System Packages ==="
sudo apt-get update && sudo apt-get upgrade -y

echo "=== 2. Installing Python, Nginx, Certbot & WeasyPrint OS Dependencies ==="
sudo apt-get install -y \
  python3-pip \
  python3-venv \
  git \
  nginx \
  certbot \
  python3-certbot-nginx \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libpangoft2-1.0-0 \
  libharfbuzz0b \
  libcairo2 \
  libgdk-pixbuf-2.0-0 \
  libffi-dev

echo "=== 3. Setting Up Application Directory ==="
sudo mkdir -p /var/www/masarumrahCRM
sudo chown -R ubuntu:ubuntu /var/www/masarumrahCRM

# Navigate to backend directory
cd /var/www/masarumrahCRM/umrahServicesbackend

echo "=== 4. Setting Up Python Virtual Environment ==="
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 5. Applying Database Migrations to db.sqlite3 ==="
python manage.py migrate

echo "=== 6. Collecting Static Files ==="
python manage.py collectstatic --noinput

echo "=== 7. Setting Proper Directory Permissions for SQLite & Media Uploads ==="
# Ensure Gunicorn and Nginx have read/write access to db.sqlite3 and media folder
chmod 664 /var/www/masarumrahCRM/umrahServicesbackend/db.sqlite3 || true
chmod 775 /var/www/masarumrahCRM/umrahServicesbackend
mkdir -p /var/www/masarumrahCRM/umrahServicesbackend/media
chmod -R 775 /var/www/masarumrahCRM/umrahServicesbackend/media
sudo usermod -a -G www-data ubuntu

echo "=== 8. Configuring Systemd Service ==="
sudo cp /var/www/masarumrahCRM/umrahServicesbackend/deploy/masarumrah.service /etc/systemd/system/masarumrah.service
sudo systemctl daemon-reload
sudo systemctl enable masarumrah
sudo systemctl restart masarumrah

echo "=== 9. Configuring Nginx for umrahdesk.masarumrah.com ==="
sudo cp /var/www/masarumrahCRM/umrahServicesbackend/deploy/nginx_umrahdesk.conf /etc/nginx/sites-available/umrahdesk
sudo ln -sf /etc/nginx/sites-available/umrahdesk /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=== 10. Issuing Free Let's Encrypt SSL Certificate ==="
echo "Make sure your Route 53 or DNS A-Record for umrahdesk.masarumrah.com points to this EC2 Public IP before running this step!"
sudo certbot --nginx -d umrahdesk.masarumrah.com --non-interactive --agree-tos -m masarumrahservice072@gmail.com --redirect || true

echo "=== Setup Complete! Masar Umrah CRM is live at https://umrahdesk.masarumrah.com ==="

