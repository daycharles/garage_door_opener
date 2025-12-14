import sys
import importlib
import traceback

sys.path.insert(0, r'C:\Users\cd104535\PycharmProjects\PythonProject')
try:
    app = importlib.import_module('app')
    print('Imported app module OK')
    client = app.app.test_client()
    r = client.get('/')
    print('GET / ->', r.status_code)
    print('GET / data (first 200 bytes):')
    print(r.data[:200])
    s = client.get('/status')
    print('GET /status ->', s.status_code)
    try:
        print('GET /status JSON ->', s.get_json())
    except Exception as e:
        print('Failed to parse JSON:', e)
except Exception:
    traceback.print_exc()

