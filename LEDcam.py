from Adafruit_AMG88xx import Adafruit_AMG88xx
import cv2
import numpy as np
from scipy.interpolate import griddata
import time
import math
import datetime
import RPi.GPIO as GPIO

# Set up GPIO pin 17 as output
# GPIO 설정
GPIO.setmode(GPIO.BCM) # Use Broadcom pin numbering
GPIO.setup(17, GPIO.OUT)

#low range of the sensor (this will be blue on the screen)
#최소온도, 24도로 설정, 파란색으로 보임
MINTEMP = 24

#high range of the sensor (this will be red on the screen)
#최고온도, 28도, 빨간색으로 보임
MAXTEMP = 28

#how many color values we can have
#최소온도, 최고온도 사이에 있는 색깔의 갯수
COLORDEPTH = 1024

#initialize the sensor
#센서 식별
sensor = Adafruit_AMG88xx()

points = [(math.floor(ix / 8), (ix % 8)) for ix in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]

#sensor is an 8x8 grid so lets do a square
#열화상카메라 화면 크기 결정
height = 720
width = 720

#create the color map
#맵 생성
colormap = cv2.applyColorMap(np.arange(0, COLORDEPTH).reshape(1, -1).astype('uint8'), cv2.COLORMAP_JET)

#some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

#let the sensor initialize
time.sleep(.1)

#실행시 해당 내용 반복 부분
while True:
    #read the pixels
    pixels = sensor.readPixels()
    pixels = [map(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in pixels]

    #perform interpolation
    bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')

    #draw everything
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for ix, row in enumerate(bicubic):
        for jx, pixel in enumerate(row):
            color = colormap[0, constrain(int(pixel), 0, COLORDEPTH - 1)]
            cv2.rectangle(img, (int(height / 32) * ix, int(width / 32) * jx), (int(height / 32) * (ix+1), int(width / 32) * (jx+1)), color.tolist(), -1)

    #show image
    #나타나는 이미지맵 화면 이름
    cv2.imshow('Heatmap', img)

    #Calculate the percentage of pixels that have risen above the baseline temperature
    #계산부분
    percentage = (np.sum(bicubic > ((MAXTEMP-MINTEMP)/2 + MINTEMP)) / (32*32)) * 100

    #Check if the percentage of pixels that have risen above the baseline temperature is more than 20%
    #기준치 온도를 설정하고, 픽셀이 변한 갯수가 전체의 20%가 되면 아래의 프린트문 출력, 시간과 문구
    #그리고 20%이상이면 신호 1을 내보내준다
    if percentage > 20: # Change this line as per your requirement
        print(f"인체연속감지중: {percentage}% detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        GPIO.output(17, GPIO.HIGH) # Set GPIO 17 to HIGH
    else:
        GPIO.output(17, GPIO.LOW)  # Set GPIO 17 to LOW

    if cv2.waitKey(1) & 0xFF == ord('q'): # Press q to quit
        break

cv2.destroyAllWindows()
