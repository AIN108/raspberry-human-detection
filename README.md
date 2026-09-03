# Raspberry Human Detection

Raspberry Pi에서 열화상 센서와 GPIO 입력 신호를 이용해 인체 또는 센서 활성 상태를 감지하는 코드 모음입니다.

```text
raspberry-human-detection/
├── LEDcam.py
├── four.py
├── requirements.txt
├── LICENSE
└── README.md
```

## 프로젝트 환경

현재 코드는 Raspberry Pi의 BCM GPIO와 I2C를 직접 사용하는 **라즈베리파이 전용 구현**입니다.

권장 기준 환경:

- Raspberry Pi 3 / 4 계열의 40핀 GPIO 환경
- Raspberry Pi OS 계열
- Python 3
- I2C 활성화 필요
- AMG8833/AMG88xx 8×8 Grid-EYE 열화상 센서

`RPi.GPIO`와 과거 Adafruit `Adafruit_AMG88xx` Python 드라이버를 사용하는 코드이므로, Raspberry Pi 5나 최신 GPIO 스택에서는 별도 호환성 확인이 필요합니다.

현재 `LEDcam.py`는 Adafruit가 2018년에 deprecated 처리한 구형 `Adafruit_AMG88xx_python` API(`from Adafruit_AMG88xx import Adafruit_AMG88xx`)를 그대로 보존합니다. 기능 보존을 위해 이번 정리에서는 드라이버 API를 바꾸지 않았습니다. 신규 구현은 Adafruit가 현재 유지하는 `adafruit-circuitpython-amg88xx` 계열로 이전하는 것이 적절합니다.

## 설치

I2C를 활성화합니다.

```bash
sudo raspi-config
```

`Interface Options`에서 I2C를 활성화한 뒤 재부팅합니다.

Python 의존성 설치:

```bash
python3 -m pip install -r requirements.txt
```

Raspberry Pi OS 환경에 따라 OpenCV는 pip 대신 시스템 패키지를 사용하는 편이 더 안정적일 수 있습니다.

```bash
sudo apt update
sudo apt install -y python3-opencv
```

## AMG8833 연결

AMG8833은 I2C 센서입니다. 일반적인 Raspberry Pi 40핀 헤더의 I2C1 기준 연결은 다음과 같습니다.

| AMG8833 | Raspberry Pi | 물리 핀 |
|---|---|---:|
| VIN / VCC | 3.3V 또는 보드가 지원하는 전원 입력 | 1 또는 17 |
| GND | GND | 6 등 |
| SDA | GPIO2 / SDA1 | 3 |
| SCL | GPIO3 / SCL1 | 5 |

센서 보드의 전원 허용 범위는 사용하는 AMG8833 breakout 보드 사양을 우선 확인하세요. Adafruit breakout은 I2C를 사용하며 기본 주소는 보드 설정에 따라 일반적으로 `0x69` 계열입니다.

연결 확인 예:

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

## 핀 구성

두 프로그램을 같은 Raspberry Pi에서 동시에 실행할 수 있도록 출력 핀을 분리했습니다.

| 프로그램 | 역할 | BCM GPIO | 물리 핀 |
|---|---|---:|---:|
| `LEDcam.py` | AMG88xx 열화상 감지 결과 출력 | `27` | 13 |
| `four.py` | 여러 디지털 입력의 집계 결과 출력 | `17` | 11 |

`four.py`의 입력 핀은 다음과 같습니다.

| BCM | 물리 핀 |
|---:|---:|
| 21 | 40 |
| 26 | 37 |
| 20 | 38 |
| 16 | 36 |
| 19 | 35 |
| 13 | 33 |
| 12 | 32 |
| 6 | 31 |
| 5 | 29 |

```python
INPUT_PINS = [21, 26, 20, 16, 19, 13, 12, 6, 5]
OUTPUT_PIN = 17
```

`LEDcam.py`는 다음 출력 핀을 사용합니다.

```python
OUTPUT_PIN = 27
```

두 스크립트는 BCM 번호 체계를 사용합니다.

## LEDcam.py

`Adafruit_AMG88xx` 8×8 열화상 센서 데이터를 읽어 OpenCV 열지도로 표시하고, 설정된 온도 범위를 기준으로 활성 픽셀 비율을 계산합니다.

현재 주요 설정:

- 최소 온도: `24°C`
- 최대 온도: `28°C`
- 센서 입력: AMG88xx 8×8
- 보간 출력: 32×32
- 표시 크기: 720×720
- 컬러맵: OpenCV `COLORMAP_JET`
- 감지 기준: 계산된 픽셀 비율이 `20%` 초과
- 감지 출력: BCM GPIO `27` HIGH
- 미감지 출력: BCM GPIO `27` LOW
- 종료: `q` 또는 `Ctrl+C`

처리 흐름:

```text
AMG88xx 8×8 열 데이터
        ↓
24~28°C 범위 매핑
        ↓
32×32 cubic interpolation
        ↓
OpenCV heatmap 출력
        ↓
기준 온도 이상 픽셀 비율 계산
        ↓
20% 초과 ──→ GPIO27 HIGH
20% 이하 ──→ GPIO27 LOW
```

실행:

```bash
python3 LEDcam.py
```

종료 시 GPIO27을 LOW로 내린 뒤 해당 핀을 정리하도록 되어 있습니다.

## four.py

여러 GPIO 입력의 상태를 약 0.1초 간격으로 읽고, 입력 중 하나라도 HIGH이면 GPIO17을 HIGH로 출력합니다.

처리 흐름:

```text
GPIO 21 ─┐
GPIO 26 ─┤
GPIO 20 ─┤
GPIO 16 ─┤
GPIO 19 ─┤
GPIO 13 ─┼─→ 하나라도 HIGH → GPIO17 HIGH
GPIO 12 ─┤
GPIO  6 ─┤
GPIO  5 ─┘

모두 LOW → GPIO17 LOW
```

실행:

```bash
python3 four.py
```

종료:

```text
Ctrl+C
```

종료 또는 예외 발생 시 GPIO17을 LOW로 내린 뒤 프로그램이 사용한 GPIO 핀만 정리합니다.

## 동시에 사용할 경우

현재 핀 배치는 서로 충돌하지 않습니다.

```text
LEDcam.py
AMG88xx → 열화상 판정 → GPIO27

four.py
GPIO 21/26/20/16/19/13/12/6/5 → OR 집계 → GPIO17
```

두 출력은 서로 독립적입니다. GPIO27의 열화상 감지 결과를 `four.py`의 집계 입력에 포함시키려면 별도의 하드웨어 연결 또는 코드 통합이 필요합니다.

## 처리속도 / 벤치마크

AMG8833 센서 자체의 최대 프레임레이트는 최대 약 10 Hz이므로 센서 입력 단계의 이론적 상한이 존재합니다. 다만 이 저장소의 실제 Raspberry Pi 처리속도는 아직 동일 조건으로 실측·기록하지 않았습니다.

따라서 다음과 같은 숫자는 현재 README에서 임의로 주장하지 않습니다.

- 실제 FPS
- 프레임당 지연시간
- CPU 사용률
- 메모리 사용량
- 전력 소비

실측할 때는 아래 조건을 함께 기록하는 것을 권장합니다.

```text
Raspberry Pi 모델:
Raspberry Pi OS 버전:
Python 버전:
OpenCV 버전:
AMG8833 드라이버:
출력 해상도: 720×720
보간 크기: 32×32
측정 시간: 60초 이상
평균 FPS:
평균 CPU 사용률:
메모리 사용량:
```

센서 자체가 최대 10 Hz급이므로 실제 응용에서는 단순 최고 FPS보다 **센서 갱신 주기 내에서 보간·표시·GPIO 판정이 안정적으로 완료되는지**를 확인하는 것이 더 중요합니다.

## 하드웨어 주의

- GPIO 번호는 **BCM 번호**입니다.
- Raspberry Pi GPIO에는 3.3V 논리 신호를 사용해야 합니다.
- 외부 센서와 Raspberry Pi 사이에는 공통 GND가 필요합니다.
- 입력 장치가 자체적으로 HIGH/LOW를 확실히 구동하지 않는 경우 입력이 떠 있을 수 있으므로 외부 풀업/풀다운 구성 확인이 필요합니다.
- I2C의 SDA/SCL 라인은 일반 GPIO 출력처럼 임의로 구동하지 마세요.

## 출처 및 라이선스

이 저장소의 `LEDcam.py`에서 사용하는 AMG88xx 열화상 보간·시각화 구조는 Adafruit의 공개 AMG8833 Raspberry Pi thermal camera 예제 계열을 참고해 정리·수정한 코드입니다.

- Adafruit AMG8833 guide: https://learn.adafruit.com/adafruit-amg8833-8x8-thermal-camera-sensor
- Adafruit maintained CircuitPython driver: https://github.com/adafruit/Adafruit_CircuitPython_AMG88xx
- Legacy driver used by current code: https://github.com/adafruit/Adafruit_AMG88xx_python

Adafruit 예제 및 드라이버는 각 원본 저장소의 라이선스를 따릅니다. 현재 구형 Python 드라이버 저장소는 Adafruit에 의해 archived/deprecated된 상태입니다.

이 저장소에서 AIN108이 작성·수정한 코드 부분은 루트의 `LICENSE`에 명시한 MIT License로 배포합니다. 외부 라이브러리와 하드웨어 드라이버는 각 프로젝트의 별도 라이선스를 따릅니다.

## 참고

이 저장소는 기존 프로젝트에서 사용하던 코드를 정리하고, 두 프로그램의 GPIO 출력 충돌을 제거한 버전입니다. 실제 지원 범위는 Raspberry Pi 모델, Raspberry Pi OS, Python, OpenCV, GPIO 백엔드 및 AMG88xx 드라이버 버전에 따라 달라질 수 있습니다.
