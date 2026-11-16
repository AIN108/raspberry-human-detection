"""LEDcam.py 열화상 판정과 four.py 입력 집계 테스트 (하드웨어 없이)."""
import re
import sys
import time
import types

import cv2
import pytest

OUTPUT_LEDCAM, OUTPUT_FOUR = 27, 17
PERSON_PIXELS = (18, 19, 20, 26, 27, 28, 34, 35, 36, 42, 43, 44, 50, 51, 52)  # 가운데 3×5 영역


@pytest.fixture
def ledcam(gpio, run_script, monkeypatch):
    """센서가 주어진 64픽셀 온도를 돌려주게 하고 LEDcam.py를 1프레임만 실행한다."""
    monkeypatch.setattr(cv2, "imshow", lambda *a, **k: None)
    monkeypatch.setattr(cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(cv2, "waitKey", lambda *a: ord("q"))  # 첫 프레임 처리 후 종료

    def _run(pixels):
        sensor_module = types.ModuleType("Adafruit_AMG88xx")

        class Sensor:
            def readPixels(self):
                return list(pixels)

        sensor_module.Adafruit_AMG88xx = Sensor
        monkeypatch.setitem(sys.modules, "Adafruit_AMG88xx", sensor_module)
        gpio["outputs"].clear()
        out = run_script("LEDcam.py")
        first = [value for pin, value in gpio["outputs"] if pin == OUTPUT_LEDCAM][0]  # 판정 결과(종료 시 LOW 제외)
        match = re.search(r"([\d.]+)% detected", out)
        return first, float(match.group(1)) if match else None

    return _run


@pytest.mark.parametrize("temperature", [24.0, 24.2, 25.0, 25.9])
def test_uniform_background_below_26c_is_not_detected(ledcam, temperature):
    # 수정 전에는 기준이 약 24.1°C여서 24.2°C 이상 배경만으로 100% 감지되었다
    detected, _ = ledcam([temperature] * 64)
    assert detected == 0


@pytest.mark.parametrize("temperature", [26.1, 27.0])
def test_uniform_scene_above_26c_is_detected(ledcam, temperature):
    detected, percentage = ledcam([temperature] * 64)
    assert detected == 1 and percentage == pytest.approx(100.0)


def test_person_on_cool_background_is_detected_with_partial_ratio(ledcam):
    pixels = [24.5] * 64
    for i in PERSON_PIXELS:
        pixels[i] = 31.0
    detected, percentage = ledcam(pixels)
    assert detected == 1
    assert 20 < percentage < 60  # 배경은 포함하지 않는다 (수정 전에는 약 84%)


def test_ledcam_releases_output_pin(ledcam, gpio):
    ledcam([24.0] * 64)
    assert gpio["outputs"][-1] == (OUTPUT_LEDCAM, 0)
    assert gpio["cleanup"] == [OUTPUT_LEDCAM]


@pytest.mark.parametrize("active,expected", [((), 0), ((26,), 1), ((21, 5), 1)])
def test_four_ors_input_pins(gpio, run_script, monkeypatch, active, expected):
    gpio["inputs"].update({pin: 1 for pin in active})
    monkeypatch.setattr(time, "sleep", lambda _: (_ for _ in ()).throw(KeyboardInterrupt()))
    run_script("four.py")
    assert gpio["outputs"][0] == (OUTPUT_FOUR, expected)
    assert gpio["outputs"][-1] == (OUTPUT_FOUR, 0)  # 종료 시 LOW
    assert gpio["cleanup"] == [[21, 26, 20, 16, 19, 13, 12, 6, 5, OUTPUT_FOUR]]
