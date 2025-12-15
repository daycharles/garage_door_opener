import socket
import sys
import time

# Find a free port on localhost
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('127.0.0.1', 0))
    s.listen(1)
    port = s.getsockname()[1]

print(f"Starting app on 127.0.0.1:{port}")

# Import the package app and run it
from app import app as flask_app

try:
    flask_app.run(host='127.0.0.1', port=port)
except Exception as e:
    print('Failed to start app:', e)
    sys.exit(1)

