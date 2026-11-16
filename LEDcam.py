from Adafruit_AMG88xx import Adafruit_AMG88xx
import cv2
import numpy as np
from scipy.interpolate import griddata
import time
import math
import datetime
import RPi.GPIO as GPIO

# BCM GPIO numbering
OUTPUT_PIN = 27
MINTEMP = 24
MAXTEMP = 28
COLORDEPTH = 1024
DETECTION_THRESHOLD_PERCENT = 20

GPIO.setmode(GPIO.BCM)
GPIO.setup(OUTPUT_PIN, GPIO.OUT, initial=GPIO.LOW)

# AMG88xx 8x8 thermal sensor
sensor = Adafruit_AMG88xx()

points = [(math.floor(ix / 8), ix % 8) for ix in range(64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]

height = 720
width = 720

colormap = cv2.applyColorMap(
    np.arange(0, COLORDEPTH).reshape(1, -1).astype("uint8"),
    cv2.COLORMAP_JET,
)


def constrain(value, minimum, maximum):
    return min(maximum, max(minimum, value))


def map_range(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


time.sleep(0.1)

try:
    while True:
        pixels = sensor.readPixels()
        pixels = [
            map_range(pixel, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1)
            for pixel in pixels
        ]

        bicubic = griddata(points, pixels, (grid_x, grid_y), method="cubic")

        if bicubic is None or np.isnan(bicubic).all():
            raise RuntimeError("AMG88xx 열화상 데이터를 보간할 수 없습니다.")

        image = np.zeros((height, width, 3), dtype=np.uint8)
        for ix, row in enumerate(bicubic):
            for jx, pixel in enumerate(row):
                if np.isnan(pixel):
                    pixel = 0
                color = colormap[0, constrain(int(pixel), 0, COLORDEPTH - 1)]
                cv2.rectangle(
                    image,
                    (int(height / 32) * ix, int(width / 32) * jx),
                    (int(height / 32) * (ix + 1), int(width / 32) * (jx + 1)),
                    color.tolist(),
                    -1,
                )

        cv2.imshow("Heatmap", image)

        threshold_temperature = (MAXTEMP - MINTEMP) / 2 + MINTEMP
        # bicubic은 0~COLORDEPTH-1 색상 인덱스로 변환된 값이므로 기준 온도도 같은 단위로 바꿔 비교한다.
        threshold_index = map_range(
            threshold_temperature, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1
        )
        percentage = (
            np.sum(bicubic > threshold_index) / bicubic.size
        ) * 100

        detected = percentage > DETECTION_THRESHOLD_PERCENT
        GPIO.output(OUTPUT_PIN, GPIO.HIGH if detected else GPIO.LOW)

        if detected:
            print(
                f"인체연속감지중: {percentage:.2f}% detected at "
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    pass
finally:
    GPIO.output(OUTPUT_PIN, GPIO.LOW)
    GPIO.cleanup(OUTPUT_PIN)
    cv2.destroyAllWindows()
