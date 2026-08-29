import RPi.GPIO as GPIO
import time

# Setup the GPIO pin numbering system
#gpio 시스템 받아서
GPIO.setmode(GPIO.BCM)

# Define the input and output pins
#정보 받는 핀, 나가는 핀 설정
input_pins = [21,26,20,16,19,13,12,6,5]
output_pin = 17

# Setup the input pins
for pin in input_pins:
    GPIO.setup(pin, GPIO.IN)

# Setup the output pin
GPIO.setup(output_pin, GPIO.OUT)

#실행하면 이 부분 반복
try:
    while True:
        # Get the state of the input pins
        pin_states = [GPIO.input(pin) for pin in input_pins]
        #pir에서 전송되는 정보 출력
        print("Pin states: ", pin_states)

        # If any pin state is 1, set output to 1, else 0
        #1이 하나라도 오면 1을 내보내고, 아닐 경우는 0을 내보낸다
        if any(pin_states):
            GPIO.output(output_pin, GPIO.HIGH)
        else:
            GPIO.output(output_pin, GPIO.LOW)

        # Wait for a short period before checking again
        #몇초마다할지 결정
        time.sleep(0.1)

except KeyboardInterrupt:
    # Reset the GPIO pins on a Keyboard Interrupt to exit
    GPIO.cleanup()
