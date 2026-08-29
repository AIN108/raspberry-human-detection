import time
import RPi.GPIO as GPIO

# BCM GPIO numbering
INPUT_PINS = [21, 26, 20, 16, 19, 13, 12, 6, 5]
OUTPUT_PIN = 17
POLL_INTERVAL_SECONDS = 0.1

GPIO.setmode(GPIO.BCM)

for pin in INPUT_PINS:
    GPIO.setup(pin, GPIO.IN)

GPIO.setup(OUTPUT_PIN, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        pin_states = [GPIO.input(pin) for pin in INPUT_PINS]
        print("Pin states:", pin_states)

        any_active = any(pin_states)
        GPIO.output(OUTPUT_PIN, GPIO.HIGH if any_active else GPIO.LOW)

        time.sleep(POLL_INTERVAL_SECONDS)

except KeyboardInterrupt:
    pass
finally:
    GPIO.output(OUTPUT_PIN, GPIO.LOW)
    GPIO.cleanup(INPUT_PINS + [OUTPUT_PIN])
