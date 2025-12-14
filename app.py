import os
import time
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config
import gpio

# App metadata
app = Flask(__name__, static_folder='static')
CORS(app)

# Rate limiter (configured per-route)
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])

# Logging setup
log_dir = os.path.dirname(config.LOG_FILE) or 'logs'
os.makedirs(log_dir, exist_ok=True)
handler = RotatingFileHandler(config.LOG_FILE, maxBytes=5_242_880, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

START_TIME = time.time()

# Ensure GPIO is initialized once in a compatibility-safe way
_INITIALIZED = False


@app.before_request
def ensure_started():
    global _INITIALIZED
    if _INITIALIZED:
        return
    try:
        gpio.init(config.RELAY_PIN)
        app.logger.info(f"GPIO initialized on pin {config.RELAY_PIN}")
    except Exception as e:
        app.logger.exception("Failed to initialize GPIO: %s", e)
    _INITIALIZED = True


@app.route('/')
def index():
    """Serve the static HTML page with the "Open Garage" button."""
    return send_from_directory(app.static_folder, 'index.html')


def _check_token(req):
    token = req.args.get('token')
    if not token:
        return False, (jsonify({'success': False, 'error': 'Missing token'}), 401)
    if token != config.TOKEN:
        return False, (jsonify({'success': False, 'error': 'Invalid token'}), 403)
    return True, None


@app.route('/trigger', methods=['GET', 'POST'])
@limiter.limit(config.RATE_LIMIT)
def trigger():
    """Activate the relay for the configured pulse duration."""
    ok, err = _check_token(request)
    if not ok:
        return err

    client_ip = request.remote_addr or 'unknown'
    try:
        ts = gpio.trigger_pulse(config.PULSE_SECONDS)
        app.logger.info(f"Triggered by {client_ip} at {ts}")
        return jsonify({'success': True, 'timestamp': ts, 'client_ip': client_ip})
    except Exception as e:
        app.logger.exception("GPIO error on trigger: %s", e)
        return jsonify({'success': False, 'error': 'GPIO error', 'details': str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    """Return uptime and last trigger time."""
    uptime = time.time() - START_TIME
    status = gpio.get_status()
    return jsonify({'uptime_seconds': round(uptime, 2), 'gpio': status})


if __name__ == '__main__':
    # Choose host and try ports in order. Prefer 8001 then 8002 when no PORT env is set.
    import platform, socket, sys

    default_host = '127.0.0.1' if platform.system() == 'Windows' else '0.0.0.0'
    host = os.environ.get('HOST', default_host)

    # If user provided PORT env, use it only. Otherwise try preferred ports 8001, 8002.
    env_port = os.environ.get('PORT')
    if env_port:
        try:
            candidate_ports = [int(env_port)]
        except ValueError:
            app.logger.warning('Invalid PORT env value %r, falling back to defaults', env_port)
            candidate_ports = [8001, 8002]
    else:
        candidate_ports = [8001, 8002]

    started = False
    for port in candidate_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            sock.close()
        except OSError as e:
            app.logger.warning('Port %s not available on %s: %s', port, host, e)
            sock.close()
            continue

        # Port is available — start the Flask server
        try:
            app.logger.info('Starting Garage Door app on %s:%s', host, port)
            app.run(host=host, port=port)
            started = True
            break
        except Exception as e:
            app.logger.exception('Failed to start server on %s:%s: %s', host, port, e)
            # If it fails unexpectedly, try next port
            continue

    if not started:
        app.logger.error('Unable to bind to any candidate ports: %s', candidate_ports)
        print('Failed to bind to any port:', candidate_ports)
        sys.exit(1)
