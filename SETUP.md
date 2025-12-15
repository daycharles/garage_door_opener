# Raspberry Pi Zero W — Garage Door Opener Setup Guide

This document covers everything to get your Raspberry Pi Zero W running the garage door opener Flask app included in this repository. It includes hardware wiring, software installation, configuration, running as a systemd service, testing, logging, troubleshooting, and security recommendations.

> Important safety note: a garage wall-button is a low‑voltage dry contact in most openers and is safe to switch with a small relay. Do not wire relay contacts directly to mains or to the garage motor unless you are absolutely sure the relay and wiring are rated; consult an electrician if unsure.


## Quick checklist

- [ ] Flash Raspberry Pi OS to microSD and enable SSH/Wi‑Fi if headless
- [ ] Wire relay to Pi (5V, GND, GPIO17) and relay COM/NO in parallel with garage button
- [ ] Copy project to Pi and create a Python virtualenv
- [ ] Install Python dependencies from `requirements.txt`
- [ ] Set `GARAGE_TOKEN` environment variable (strong secret)
- [ ] Start the app (it will try ports 8001, 8002 by default)
- [ ] Test using the web UI or curl
- [ ] Install and enable the systemd service for automatic start on boot


## Parts required

- Raspberry Pi Zero W (microSD card, power supply)
- Single‑channel 5V relay module (optically isolated recommended)
- Jumper wires and small screwdriver
- (Optional) Multimeter


## Wiring overview

- Relay control pins (module side): VCC, GND, IN
- Relay screw terminals (switch): COM, NO, NC (we use COM & NO)

Signal wiring (Pi BCM numbering):

- Relay IN  -> Raspberry Pi GPIO 17 (BCM17)  — Pi physical pin 11
- Relay VCC -> Pi 5V (physical pin 2 or 4)
- Relay GND -> Pi GND (physical pin 6 or other GND)

Switched contact (in parallel to wall button):

- Relay COM -> Garage opener terminal 1 (where the wall button connects)
- Relay NO  -> Garage opener terminal 2

This configuration closes COM ↔ NO while the relay is triggered, simulating a momentary button press.


### Pin map (partial)

- Physical pin 2 — 5V
- Physical pin 6 — GND
- Physical pin 11 — GPIO17 (BCM17)


## Notes about relay modules

- Some relay modules are active LOW (they energize when the input is pulled low). If your module behaves this way you'll either invert the software logic (set LOW to trigger) or use a different module/driver.
- Many small relay boards are designed for 5V logic. They usually still work with a 3.3V GPIO control line, but test carefully before wiring the opener. If necessary, use a transistor or opto coupler input wiring per the module's docs.
- If the module advertises "opto‑isolated," check whether you must tie module GND to Pi GND for the input to work; follow module docs.


## Prepare the Raspberry Pi (headless or with display)

1. Flash Raspberry Pi OS (Lite or Desktop) to your microSD card using Raspberry Pi Imager or balenaEtcher.
2. (Optional headless) Enable SSH and Wi‑Fi on first boot:
   - Place an empty file named `ssh` in the `boot` partition.
   - Create `wpa_supplicant.conf` in `boot` with Wi‑Fi credentials (see Raspberry Pi docs for format).
3. Boot the Pi and SSH in:

```bash
# Example
ssh dtfitness@192.168.0.34
```

4. Update the Pi:

```bash
sudo apt update
sudo apt upgrade -y
```


## Software install on the Pi (step-by-step)

From `/home/dtfitness/Desktop/PythonProject` (or your chosen directory):

```bash
# Clone repository (replace <repo-url> if using git)
cd /home/dtfitness/Desktop/PythonProject
git clone https://github.com/daycharles/garage_door_opener.git garage
cd garage

# Create virtualenv and activate
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you don't use `git`, copy the project folder to `/home/dtfitness/Desktop/PythonProject` using `scp` or another network‑transfer method.

Network transfer examples (recommended):

1) Using `git` on the Pi (preferred if the repo is hosted remotely):

```bash
cd /home/pi
git clone https://github.com/daycharles/garage_door_opener.git garage
cd garage
```

2) Using `scp` from your workstation to the Pi:

From a Windows PowerShell with OpenSSH installed (or a Linux/macOS terminal):

```powershell
# Windows PowerShell example
# Adjust the source path and <pi-ip>
scp -r C:\Users\<dtfitness>\Desktop\PythonProject\garage_door_opener\ pi@<pi-ip>:/home/pi/garage
```

```bash
# Linux/macOS example
scp -r ~/Desktop/garage/garage_door_opener pi@<pi-ip>:/home/pi/garage
```

After the project is present on the Pi, you can use the included installer script to automate setup. For example:

```bash
# run from the Pi (make sure file is executable)
cd /home/pi/garage
chmod +x install_pi.sh
sudo bash install_pi.sh /home/pi/garage /home/pi/garage/garage-door.env
```

The installer script will:

- create a Python virtual environment and install dependencies from `requirements.txt`
- copy the provided `garage-door.env` into `/etc/default/garage-door` (if present)
- install the `garage-door.service` systemd unit, enable and start it

If you prefer manual steps, follow the earlier commands to create the venv and install dependencies.


## Configuration

Configuration values live in `config.py` and can be overridden by environment variables. Recommended production configuration uses environment variables (or an `EnvironmentFile` with systemd).

Key settings:

- `GARAGE_TOKEN` (environment variable) — the shared secret token used to authorize /trigger requests. Change it from the default `changeme-token`.
- `RELAY_PIN` — BCM pin number (default 17)
- `PULSE_SECONDS` — how long to hold the relay (default 0.5)
- `RATE_LIMIT` — Flask-Limiter rule (default `1 per 3 seconds`)
- `LOG_FILE` — path to logs (default `logs/garage.log`)

Set env vars for the current shell (example):

```bash
export GARAGE_TOKEN='replace-with-a-strong-random-token'
export RELAY_PIN='17'
export PULSE_SECONDS='0.5'
export RATE_LIMIT='1 per 3 seconds'
export PORT='8001'   # optional: force a port
```


## Running the app (development)

Activate the virtualenv and run the app. The app will try configured port(s). On Linux the app's default behavior is to try ports 8001 then 8002 if `PORT` is not set.

```bash
source .venv/bin/activate
python app.py
```

You should see logs indicating which port the app bound to. Example:

```
INFO Starting Garage Door app on 0.0.0.0:8001
```

Open the UI in a browser: `http://<pi-ip>:8001/` (replace port if different).


## Running the app with systemd (recommended for Boot)

Create an environment file `/etc/default/garage-door` (recommended) containing secrets:

```ini
# /etc/default/garage-door
GARAGE_TOKEN=replace-with-a-strong-random-token
PORT=8001
```

Create the systemd unit `/etc/systemd/system/garage-door.service` (example):

```ini
[Unit]
Description=Garage Door Opener Flask App
After=network.target

[Service]
Type=simple
User=dtfitness
WorkingDirectory=/home/dtfitness/Desktop/PythonProject
ExecStart=/home/dtfitness/Desktop/PythonProject/.venv/bin/python /home/dtfitness/Desktop/PythonProject/app.py
Restart=on-failure
EnvironmentFile=/etc/default/garage-door

[Install]
WantedBy=multi-user.target
```

Alternatively, keep the unit file in the project repo and have systemd use it directly (editable in your repo):

```bash
# from your project directory on the Pi
sudo systemctl link /home/dtfitness/Desktop/PythonProject/garage-door.service
sudo systemctl daemon-reload
sudo systemctl enable --now garage-door.service
```

Enable and start the service (if you copied the unit to /etc/systemd/system):

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now garage-door.service
sudo systemctl status garage-door.service
sudo journalctl -u garage-door -f
```

Notes:
- If you must access GPIO and the service fails with permission errors, ensure the configured `User=` in the service has access to GPIO (usually the default pi or the locally used user `dtfitness`).


## Testing endpoints (examples)

Replace `<pi-ip>` and `<token>` as appropriate.

- Status endpoint:
```bash
curl "http://<pi-ip>:8001/status"
```

- Trigger (GET):
```bash
curl "http://<pi-ip>:8001/trigger?token=<token>"
```

- Trigger (POST):
```bash
curl -X POST "http://<pi-ip>:8001/trigger?token=<token>"
```

The app also includes a simple static UI at `/` with a button labeled "Open Garage" which prompts for token and calls `/trigger`.


## Logs

- Default app log: `logs/garage.log` (relative to the project dir). The app uses a RotatingFileHandler.

To view logs:

```bash
tail -f logs/garage.log
# or systemd
sudo journalctl -u garage-door -f
```

Log entries include timestamp and client IP for each trigger.


## Troubleshooting

- App won't start (port bind error): choose a different port or ensure no OS-level URL reservations exist (Windows). On Pi this is uncommon.
- Relay does not switch:
  - Check wiring (VCC, GND, IN), confirm the relay LED toggles when you call the endpoint.
  - If relay module is active LOW, invert logic or change module wiring.
  - If module requires 5V logic and won't trigger with 3.3V, use a transistor/driver.
- Permission errors when accessing GPIO: test running the script with `sudo` to verify permissions are the issue.
- Token errors: ensure `GARAGE_TOKEN` is set correctly and you include it when calling `/trigger`.


## Security recommendations

- Change the default token immediately and keep it outside source control (use environment variables or `/etc/default/garage-door`).
- Avoid exposing the Pi directly to the public internet. If you need remote access, put it behind a reverse proxy (nginx) with HTTPS and authenticated access.
- Prefer Authorization header (Bearer token) instead of query string to avoid token leakage in logs/history — I can update the app to accept header tokens.
- Use `ufw` to restrict access to your LAN if you want:

```bash
sudo apt install ufw
sudo ufw allow from 192.168.1.0/24 to any port 8001
sudo ufw enable
```

- For robust rate-limiting across reboots/multiple processes, configure Flask-Limiter with Redis storage instead of the default in-memory store.


## GPIO & Hardware safety checklist (before testing with the opener)

1. With power off, connect COM/NO to the two terminals currently used by the wall button so the relay is in parallel with the button.
2. Connect relay VCC and GND to the Pi, but keep the garage opener powered off while verifying basic relay function first if possible.
3. Power the Pi and run `python app.py`. Test trigger with curl and listen for the relay click.
4. If relay click works, power on the garage opener and try a single trigger while standing at a safe distance.


## Optional improvements & next steps

- Switch authentication to `Authorization: Bearer <token>` header (more private than query string).
- Add optional two-factor or password-protected UI for the local button.
- Add Redis backend for Flask-Limiter for persistence.
- Add hardware debounce or minimum-interval checks in software to prevent repeated triggering.


## Example commands summary (copy/paste)

On the Pi (one-line copy/paste):

```bash
cd /home/pi && git clone <your-repo-url> garage && cd garage && python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -r requirements.txt
```

Set token and run:

```bash
export GARAGE_TOKEN='replace-with-a-strong-random-token'
source .venv/bin/activate
python app.py
```

Test (from another machine):

```bash
curl "http://<pi-ip>:8001/trigger?token=replace-with-a-strong-random-token"
```


---

If you'd like, I can also:

- Update the app to accept `Authorization: Bearer <token>` header and show example curl commands.
- Create `/etc/default/garage-door` and the `garage-door.service` file in the repo ready to `scp` to the Pi.
- Add an FAQ or troubleshooting checklist tailored to your specific relay module if you share its model.

Which of these would you like next?
