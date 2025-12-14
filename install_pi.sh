#!/bin/bash
set -euo pipefail

# Usage: sudo bash install_pi.sh /path/to/project
# This script installs the garage-door app on a Raspberry Pi.
# It expects the project to be copied to the provided directory (e.g. /home/pi/garage).

TARGET_DIR=${1:-/home/pi/garage}
ENV_FILE=${2:-${TARGET_DIR}/garage-door.env}
SERVICE_FILE=${3:-${TARGET_DIR}/garage-door.service}

echo "Installing Garage Door app to: $TARGET_DIR"

if [ ! -d "$TARGET_DIR" ]; then
  echo "Target directory $TARGET_DIR does not exist. Copy the project to the Pi and re-run this script." >&2
  exit 2
fi

# Ensure apt packages exist
echo "Updating apt and installing required packages..."
apt update
apt install -y python3-venv python3-pip git

# Create venv
cd "$TARGET_DIR"
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Copy env file into /etc/default/garage-door if provided
if [ -f "$ENV_FILE" ]; then
  echo "Installing environment file to /etc/default/garage-door"
  sudo cp "$ENV_FILE" /etc/default/garage-door
  sudo chown root:root /etc/default/garage-door
  sudo chmod 640 /etc/default/garage-door
else
  echo "No env file found at $ENV_FILE; create /etc/default/garage-door manually or pass as second arg." >&2
fi

# Install systemd unit
if [ -f "$SERVICE_FILE" ]; then
  echo "Installing systemd unit to /etc/systemd/system/garage-door.service"
  sudo cp "$SERVICE_FILE" /etc/systemd/system/garage-door.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now garage-door.service
  echo "Enabled and started garage-door.service"
else
  echo "No service file found at $SERVICE_FILE; create /etc/systemd/system/garage-door.service manually or pass as third arg." >&2
fi

echo "Installation complete. Use 'sudo journalctl -u garage-door -f' to view logs."
