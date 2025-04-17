import time
import board
import busio
import RPi.GPIO as GPIO
from adafruit_ads1x15.ads1015 import ADS1015 
from adafruit_ads1x15.analog_in import AnalogIn

# Constants
BUFFER_SIZE = 80
LED_PIN = 21  # GPIO 21 is physical pin 40 (BCM numbering used below)

# Initialize I2C and ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1015(i2c)
chan = AnalogIn(ads, 0) # AnalogIn(ads, ADS1015.P0) # reading from A0

# Setup GPIO for LED
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# Buffers and state
REDdat = [0.0] * BUFFER_SIZE
IRdat = [0.0] * BUFFER_SIZE
RED_head = RED_tail = RED_count = 0
IR_head = IR_tail = IR_count = 0

def push(value, buffer, state):
    head, tail, count = state
    if count == BUFFER_SIZE:
        tail = (tail + 1) % BUFFER_SIZE
    else:
        count += 1
    buffer[head] = value
    head = (head + 1) % BUFFER_SIZE
    return head, tail, count

def find_min_max(data, head, tail, count):
    if count == 0:
        return 0, 0
    min_val = float('inf')
    max_val = float('-inf')
    for i in range(count):
        idx = (tail + i) % BUFFER_SIZE
        val = data[idx]
        min_val = min(min_val, val)
        max_val = max(max_val, val)
    return min_val, max_val

def moving_average(data, head, count, window_size):
    if count == 0:
        return 0
    valid_samples = min(count, window_size)
    total = 0
    for i in range(valid_samples):
        idx = (head - 1 - i + BUFFER_SIZE) % BUFFER_SIZE
        total += data[idx]
    return total / valid_samples

try:
    while True:
        REDtemp = 0
        IRtemp = 0

        # RED LED ON
        GPIO.output(LED_PIN, GPIO.HIGH)
        for _ in range(5):
            time.sleep(0.01)
            REDtemp += chan.value * 0.2
        RED_head, RED_tail, RED_count = push(REDtemp, REDdat, (RED_head, RED_tail, RED_count))

        # IR LED ON (RED LED OFF)
        GPIO.output(LED_PIN, GPIO.LOW)
        for _ in range(5):
            time.sleep(0.01)
            IRtemp += chan.value * 0.2
        IR_head, IR_tail, IR_count = push(IRtemp, IRdat, (IR_head, IR_tail, IR_count))

        smoothedIR = moving_average(IRdat, IR_head, IR_count, 15)
        smoothedRED = moving_average(REDdat, RED_head, RED_count, 15)

        minIR, maxIR = find_min_max(IRdat, IR_head, IR_tail, IR_count)
        minRED, maxRED = find_min_max(REDdat, RED_head, RED_tail, RED_count)

        # Avoid division by zero
        if smoothedIR > 0 and smoothedRED > 0 and (maxIR - minIR) > 0:
            R = ((maxRED - minRED) / smoothedRED) / ((maxIR - minIR) / smoothedIR)
            SpO2 = 110 - 25 * R
            print(f"SpO2: {SpO2:.2f}")

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nExited cleanly.")
