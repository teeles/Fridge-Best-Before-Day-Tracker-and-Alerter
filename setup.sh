#!/bin/bash

###############################################
#  V1.0 - 21/5/2025
#  Thomas Eeles. 
#  Fridge Best Besfore Day Tracker and Alerter AKA FridgeWatch - Setup Script
###############################################

#### Variables ####
INSTALL_DIR="/opt/fridgewatch"
REPO="https://github.com/teeles/Fridge-Best-Before-Day-Tracker-and-Alerter.git"
PASS=$(openssl rand -base64 15 | tr -dc 'a-zA-Z0-9' | head -c 20)
#### Functions ####

service_user(){
  useradd --system --no-create-home --shell /usr/sbin/nologin fridge
  echo "fridge:$PASS" | chpasswd
  usermod -L fridge
  usermod -aG admin fridge
}

python_setup(){
  local REQUIRED_PKGS=(python3 python3-pip python3-venv)
  local MISSING=()

  for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! dpkg -s "$pkg" &> /dev/null; then
      echo " $pkg not found"
      MISSING+=("$pkg")
    else
      echo "$pkg is installed"
    fi
  done

  if [ ${#MISSING[@]} -ne 0 ]; then
    echo "Installing missing Python packages: ${MISSING[*]}"
    apt-get update -y
    apt-get install -y "${MISSING[@]}"
  else
    echo "All required Python packages are already installed."
  fi
}

dependacy_setup(){
  local REQUIRED_PKGS=(sqlite3 nginx git cron)
  local MISSING=()

  for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! dpkg -s "$pkg" &> /dev/null; then
      echo "$pkg not found"
      MISSING+=("$pkg")
    else
      echo "$pkg is installed"
    fi
  done

  if [ ${#MISSING[@]} -ne 0 ]; then
    echo "Installing missing packages: ${MISSING[*]}"
    apt-get update -y
    apt-get install -y "${MISSING[@]}"
  else
    echo "All system packages are already installed."
  fi
}

env_setup(){

  git clone "$REPO" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
  
  if [ -f setup.sh ]; then
    rm setup.sh
  fi
  
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  
  DB_OUTPUT=$(python3 init_db.py 2>&1)
  
  echo "$DB_OUTPUT"

  if echo "$DB_OUTPUT" | grep -qi "WARNING"; then
    echo "WARNING: There were issues initializing the database."
    echo "Check output above or manually review init_db.py"
    exit 1
  else
    echo "Database initialization successful!"
  fi 

  chown -R fridge:fridge "$INSTALL_DIR"
}

create_logs(){
  touch "$INSTALL_DIR/log/error.log"
  touch "$INSTALL_DIR/log/access.log"
  chown -R fridge:fridge "$INSTALL_DIR/log"
}

create_service(){
  cat > /etc/systemd/system/fridgewatch.service <<EOF
[Unit]
Description=FridgeWatch Web App
After=network.target

[Service]
User=fridge
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app --access-logfile log/access.log --error-logfile log/error.log --log-level info
Restart=always
RestartSec=5
Environment=PATH=$INSTALL_DIR/venv/bin

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable fridgewatch
systemctl start fridgewatch
}

nginx_setup(){
  cat > /etc/nginx/sites-available/fridgewatch <<EOF
server {
    listen 80;
    server_name _;

    location / {
      proxy_pass http://127.0.0.1:5000;
      proxy_set_header Host \$host;
      proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/fridgewatch /etc/nginx/sites-enabled/

rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
}

setup_cron(){
  local CRON_LINE="0 6 * * * /opt/fridgewatch/venv/bin/python3 /opt/fridgewatch/send_report.py --report"
  local CRON_FILE="/var/spool/cron/crontabs/fridge"

  (crontab -u fridge -l 2>/dev/null; echo "$CRON_LINE") | crontab -u fridge -
  systemctl enable cron
  systemctl restart cron
}

#### THE SCRIPT ####

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run the script using the 'sudo' command"
  exit 1
fi

if [ -d "$INSTALL_DIR" ]; then
  echo "The structure is already in place"
  echo "Running the rest of this script may break your setup"
  echo "if you want to update the app then view the readme"
  exit 1
fi

echo "This will setup FridgeWatch running on Port 80"
echo "Updating the OS"

apt update && apt upgrade -y

echo "Creating the Fridge User"

service_user

echo "Checking we have python all setup"

python_setup

echo "Checking other dependacies"

dependacy_setup

echo "getting the enviroment ready"

env_setup

echo "Creating a service so Fridge Watch will start automaticaly"

create_service

echo "Setting up a HTTP proxy so you can access fridwtach from the network"

nginx_setup

echo "setting up the daily Fridgewatch Email"

setup_cron