"""Compatibility launcher for the `app` package.

This small file preserves the ability to run `python app.py` while the
real application code lives in the `app` package. It simply imports
and delegates to the package-level `app` object.
"""

from app import app as app  # re-export package's Flask app for FLASK_APP and tests

if __name__ == '__main__':
    # Delegate to package's run logic if present
    try:
        # Many Flask apps simply call app.run() in their package; ensure we call it the same way
        app.run()
    except Exception:
        # Fallback: nothing special to do; importing the package suffices for most use-cases
        pass
