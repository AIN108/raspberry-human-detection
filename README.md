# Raspberry Human Detection

Raspberry Pi에서 열화상 센서와 GPIO 입력 신호를 이용해 인체 또는 센서 활성 상태를 감지하는 코드 모음입니다.

```text
raspberry-human-detection/
├── LEDcam.py
├── four.py
└── README.md
```

## 핀 구성

두 프로그램을 같은 Raspberry Pi에서 동시에 실행할 수 있도록 출력 핀을 분리했습니다.

| 프로그램 | 역할 | BCM GPIO |
|---|---|---:|
| `LEDcam.py` | AMG88xx 열화상 감지 결과 출력 | `27` |
| `four.py` | 여러 디지털 입력의 집계 결과 출력 | `17` |

`four.py`의 입력 핀은 다음과 같습니다.

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

필요한 Python 모듈:

- `RPi.GPIO`

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

## 하드웨어 주의

- GPIO 번호는 **BCM 번호**입니다.
- Raspberry Pi GPIO에는 3.3V 논리 신호를 사용해야 합니다.
- 외부 센서와 Raspberry Pi 사이에는 공통 GND가 필요합니다.
- 입력 장치가 자체적으로 HIGH/LOW를 확실히 구동하지 않는 경우 입력이 떠 있을 수 있으므로 외부 풀업/풀다운 구성 확인이 필요합니다.

## 참고

이 저장소는 기존 프로젝트에서 사용하던 코드를 정리하고, 두 프로그램의 GPIO 출력 충돌을 제거한 버전입니다. Raspberry Pi OS, Python, `Adafruit_AMG88xx`, `RPi.GPIO` 버전에 따라 설치 및 호환성은 별도 확인이 필요합니다.
