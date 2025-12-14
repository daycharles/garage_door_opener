"""
GPIO helper that wraps RPi.GPIO and provides a safe dummy implementation
for development on non-RPi machines.
"""
import time
import logging

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    REAL_GPIO = True
except Exception:
    # Provide a dummy GPIO for development/testing on non-RPi systems
    REAL_GPIO = False

    class DummyGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        LOW = 0
        HIGH = 1

        def __init__(self):
            self.state = {}

        def setwarnings(self, flag):
            pass

        def setmode(self, mode):
            pass

        def setup(self, pin, mode, initial=None):
            self.state[pin] = initial

        def output(self, pin, value):
            self.state[pin] = value

        def input(self, pin):
            return self.state.get(pin, 0)

        def cleanup(self):
            self.state = {}

    GPIO = DummyGPIO()


_pin = None
_last_trigger = None


def init(pin: int):
    global _pin
    _pin = pin
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(_pin, GPIO.OUT, initial=GPIO.LOW)
        logger.info(f"GPIO helper initialized pin {_pin} and set LOW")
    except Exception as e:
        logger.exception("Failed to initialize GPIO: %s", e)
        raise


def trigger_pulse(duration_seconds: float = 0.5):
    """Momentary pulse: set pin HIGH, wait duration, set LOW.

    Returns the timestamp (ISO format) when the trigger completed.
    """
    global _last_trigger
    if _pin is None:
        raise RuntimeError('GPIO not initialized')

    try:
        GPIO.output(_pin, GPIO.HIGH)
        time.sleep(duration_seconds)
        GPIO.output(_pin, GPIO.LOW)
        _last_trigger = time.time()
        ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(_last_trigger))
        return ts
    except Exception as e:
        logger.exception("Error pulsing GPIO: %s", e)
        raise


def get_status():
    return {
        'pin': _pin,
        'last_trigger': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(_last_trigger)) if _last_trigger else None,
        'is_real_gpio': REAL_GPIO,
    }


def cleanup():
    try:
        GPIO.cleanup()
    except Exception:
        pass

