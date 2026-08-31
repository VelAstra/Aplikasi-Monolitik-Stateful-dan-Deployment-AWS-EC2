#!/bin/bash
# ========================================
# Aplikasi Monolitik Stateful - Deployment
# Skrip setup otomatis di AWS EC2 (Ubuntu 22.04)
#
# Backend MURNI Python (tanpa framework), database SQLite lokal,
# manajemen sesi server-side (stateful). Tidak memerlukan PostgreSQL,
# Gunicorn, maupun Supervisor.
# ========================================

set -e

echo "========================================"
echo "Aplikasi Monolitik Stateful - Deployment"
echo "========================================"

APP_USER="appuser"
APP_HOME="/home/$APP_USER/app"
APP_NAME="app_monolitik"

echo "Step 1: Update system packages"
sudo apt-get update
sudo apt-get upgrade -y

echo "Step 2: Install dependencies"
sudo apt-get install -y \
    python3 \
    nginx \
    git \
    curl \
    wget \
    ufw

echo "Step 3: Create application user"
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash $APP_USER
    echo "User $APP_USER created"
else
    echo "User $APP_USER already exists"
fi

echo "Step 4: Clone repository"
sudo mkdir -p $APP_HOME
sudo chown $APP_USER:$APP_USER $APP_HOME
cd $APP_HOME

if [ ! -d ".git" ]; then
    sudo -u $APP_USER git clone https://github.com/VelAstra/Aplikasi-Monolitik-Stateful-dan-Deployment-AWS-EC2.git .
    echo "Repository cloned"
else
    sudo -u $APP_USER git pull origin main
    echo "Repository updated"
fi

echo "Step 5: Buat direktori log"
sudo mkdir -p $APP_HOME/logs
sudo chown $APP_USER:$APP_USER $APP_HOME/logs

echo "Step 6: Setup systemd service"
sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null <<EOF
[Unit]
Description=Aplikasi Monolitik Stateful (Pure Python)
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_HOME/src
ExecStart=/usr/bin/python3 $APP_HOME/src/app.py
Restart=always
RestartSec=3
Environment=PORT=8000
StandardOutput=append:$APP_HOME/logs/app.log
StandardError=append:$APP_HOME/logs/app_error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl start $APP_NAME
echo "Service started"

echo "Step 7: Configure Nginx"
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<'NGINX'
upstream app_server {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 20M;

    access_log /var/log/nginx/app_monolitik_access.log;
    error_log /var/log/nginx/app_monolitik_error.log;

    location / {
        proxy_pass http://app_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/appuser/app/src/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
echo "Nginx configured"

echo "Step 8: Configure UFW Firewall"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw --force enable
echo "Firewall configured"

echo "========================================"
echo "Deployment complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Status aplikasi: sudo systemctl status $APP_NAME"
echo "2. Logs: tail -f $APP_HOME/logs/app.log"
echo "3. Akses: http://your-ec2-ip"
echo ""
