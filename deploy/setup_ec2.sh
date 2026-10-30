#!/usr/bin/env bash
# ==============================================================================
# Masar Umrah CRM - AWS EC2 Turnkey Setup Script
# Domain: umrahdesk.masarumrah.com
# Database: SQLite (db.sqlite3 on this EC2 instance)
# OS: Ubuntu 22.04 / 24.04 LTS on AWS EC2
# ==============================================================================

set -e

# Detect directories and user dynamically
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_USER="$(id -un)"
CURRENT_GROUP="$(id -gn)"

echo "=== Detected Application Directory: $APP_DIR ==="
echo "=== Detected Execution User: $CURRENT_USER ==="

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

echo "=== 3. Setting Up Application Environment (.env) ==="
cd "$APP_DIR"

if [ ! -f "$APP_DIR/.env" ]; then
    echo "Creating .env from .env.example..."
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    RANDOM_SECRET=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 50 ; echo '')
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$RANDOM_SECRET/" "$APP_DIR/.env"
fi

echo "=== 4. Setting Up Python Virtual Environment ==="
python3 -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

echo "=== 5. Applying Database Migrations to db.sqlite3 ==="
python manage.py migrate

echo "=== 6. Collecting Static Files ==="
python manage.py collectstatic --noinput

echo "=== 7. Setting Proper Directory Permissions for SQLite & Media Uploads ==="
mkdir -p "$APP_DIR/media"
mkdir -p "$APP_DIR/staticfiles"
mkdir -p "$APP_DIR/logs"
chmod 664 "$APP_DIR/db.sqlite3" || true
chmod 775 "$APP_DIR"
chmod -R 775 "$APP_DIR/media"
chmod -R 775 "$APP_DIR/staticfiles"
chmod -R 775 "$APP_DIR/logs"
sudo usermod -a -G www-data "$CURRENT_USER" || true

echo "=== 8. Configuring Systemd Service ==="
sudo tee /etc/systemd/system/masarumrah.service > /dev/null <<EOF
[Unit]
Description=Gunicorn daemon for Masar Umrah CRM (umrahdesk.masarumrah.com)
After=network.target

[Service]
User=$CURRENT_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
ExecStart=$APP_DIR/.venv/bin/gunicorn \\
          --workers 3 \\
          --threads 2 \\
          --bind 127.0.0.1:8000 \\
          --timeout 120 \\
          config.wsgi:application

Restart=always
RestartSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable masarumrah
sudo systemctl restart masarumrah

echo "=== 9. Configuring Nginx for umrahdesk.masarumrah.com ==="
sudo tee /etc/nginx/sites-available/umrahdesk > /dev/null <<EOF
server {
    listen 80;
    server_name umrahdesk.masarumrah.com;

    client_max_body_size 50M;

    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, max-age=2592000";
    }

    location /media/ {
        alias $APP_DIR/media/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, max-age=2592000";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/umrahdesk /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=== 10. Issuing Free Let's Encrypt SSL Certificate ==="
echo "Note: If umrahdesk.masarumrah.com DNS points to this EC2 public IP, SSL will be provisioned automatically."
sudo certbot --nginx -d umrahdesk.masarumrah.com --non-interactive --agree-tos -m masarumrahservice072@gmail.com --redirect || echo "Certbot skipped: configure DNS A-record to enable SSL."

echo "=== Setup Complete! Masar Umrah CRM is live at https://umrahdesk.masarumrah.com ==="
