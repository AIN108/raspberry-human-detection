# Raspberry Human Detection

Raspberry Pi에서 열화상 센서와 GPIO 입력 신호를 이용해 인체 또는 센서 활성 상태를 감지하는 코드 모음입니다.

이 저장소는 두 개의 독립 실행 스크립트로 구성됩니다.

```text
raspberry-human-detection/
├── LEDcam.py
├── four.py
└── README.md
```

## LEDcam.py

`Adafruit_AMG88xx` 8×8 열화상 센서 데이터를 읽어 OpenCV 열지도로 표시하고, 설정된 온도 범위를 기준으로 활성 픽셀 비율을 계산합니다.

원본 코드의 주요 설정:

- 최소 온도: `24°C`
- 최대 온도: `28°C`
- 센서 입력: AMG88xx 8×8
- 보간 출력: 32×32
- 표시 크기: 720×720
- 컬러맵: OpenCV `COLORMAP_JET`
- 인체 감지 기준: 계산된 픽셀 비율이 `20%` 초과
- 감지 출력: BCM GPIO `17` HIGH
- 미감지 출력: BCM GPIO `17` LOW
- 종료: `q`

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
20% 초과 ──→ GPIO17 HIGH
20% 이하 ──→ GPIO17 LOW
```

필요한 Python 모듈:

- `Adafruit_AMG88xx`
- `opencv-python`
- `numpy`
- `scipy`
- `RPi.GPIO`

실행:

```bash
python3 LEDcam.py
```

## four.py

여러 GPIO 입력의 상태를 주기적으로 읽고, 입력 중 하나라도 HIGH이면 하나의 출력 신호로 합치는 GPIO 집계 코드입니다.

원본 코드의 핀 구성:

```python
input_pins = [21, 26, 20, 16, 19, 13, 12, 6, 5]
output_pin = 17
```

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

입력 상태는 약 `0.1초` 간격으로 확인하며 터미널에 현재 핀 상태를 출력합니다.

필요한 Python 모듈:

- `RPi.GPIO`

실행:

```bash
python3 four.py
```

종료는 `Ctrl+C`이며 종료 시 `GPIO.cleanup()`을 호출합니다.

## GPIO17 사용 주의

두 원본 스크립트 모두 **BCM GPIO17을 출력으로 사용합니다.**

따라서 현재 상태 그대로는 같은 Raspberry Pi에서 두 프로그램을 동시에 실행하는 구성이 아닙니다.

- `LEDcam.py`: 열화상 기반 감지 결과를 GPIO17로 출력
- `four.py`: 여러 디지털 입력을 집계한 결과를 GPIO17로 출력

두 프로그램을 동시에 운용해야 한다면 GPIO 출력 핀 설계를 먼저 분리하거나 두 기능을 하나의 프로세스로 통합해야 합니다.

## 하드웨어

`LEDcam.py`:

- Raspberry Pi
- AMG88xx 계열 8×8 열화상 센서
- GPIO17에 연결할 출력 장치 또는 후단 회로

`four.py`:

- Raspberry Pi
- GPIO 21, 26, 20, 16, 19, 13, 12, 6, 5에 연결되는 디지털 신호원
- GPIO17에 연결할 출력 장치 또는 후단 회로

## 참고

이 저장소의 코드는 기존 프로젝트에서 사용하던 원본 코드를 정리해 보관하는 목적입니다. Raspberry Pi OS 버전, Python 버전, 센서 라이브러리 버전에 따라 오래된 `Adafruit_AMG88xx` 또는 `RPi.GPIO` 의존성의 설치 방법과 호환성은 별도 확인이 필요합니다.
