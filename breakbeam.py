import RPi.GPIO as GPIO
import time
from detection import toggle_detection

GPIO.setmode(GPIO.BCM)
PIN = 17
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def watch_breakbeam():
    while True:
        if GPIO.input(PIN) == GPIO.LOW:
            toggle_detection()
            time.sleep(0.3)