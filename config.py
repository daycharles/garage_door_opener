import os

# Authentication token (override with environment variable GARAGE_TOKEN)
TOKEN = os.environ.get('GARAGE_TOKEN', 'changeme-token')

# GPIO pin (BCM mode)
RELAY_PIN = int(os.environ.get('RELAY_PIN', '17'))

# Pulse duration in seconds
PULSE_SECONDS = float(os.environ.get('PULSE_SECONDS', '0.5'))

# Log file path
LOG_FILE = os.environ.get('LOG_FILE', 'logs/garage.log')

# Rate limit for trigger endpoint (Flask-Limiter syntax)
RATE_LIMIT = os.environ.get('RATE_LIMIT', '1 per 3 seconds')

