# Raspberry Pi Garage Door Opener

Small Flask app to trigger a relay connected to a garage door opener. Designed for Raspberry Pi Zero W.

Files:
- `app.py` - main Flask application
- `config.py` - configuration (token, pin, pulse duration)
- `gpio.py` - GPIO wrapper (falls back to dummy on non-RPi)
- `static/index.html` - simple web UI
- `logs/` - log directory (app writes `logs/garage.log`)
- `garage-door.service` - example systemd unit file

Quick start (on Pi):

1. Copy the project to `/home/pi/garage`.
2. Install dependencies:

```powershell
python3 -m pip install -r requirements.txt
```

3. Set a secure token and enable the service (example):

```powershell
# Edit service file or set environment
sudo systemctl daemon-reload
sudo systemctl enable --now garage-door.service
```

Access the web UI at `http://<pi-ip>:8000/` and enter your token when prompted.

