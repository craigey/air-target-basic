import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

from detection import toggle_detection

PIN = 17

def setup_gpio():
    if not GPIO_AVAILABLE:
        print("⚠️ GPIO not available (not running on Raspberry Pi)")
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("✅ Break-beam GPIO initialized")


def watch_breakbeam():
    if not GPIO_AVAILABLE:
        return  # silently do nothing

    print("👁️ Break-beam watcher running")

    try:
        while True:
            if GPIO.input(PIN) == GPIO.LOW:
                toggle_detection()
                time.sleep(0.3)
    except KeyboardInterrupt:
        GPIO.cleanup()