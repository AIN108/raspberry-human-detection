"""Raspberry Pi·AMG8833 없이 스크립트를 실행하기 위한 스텁.

LEDcam.py·four.py는 import 시점에 GPIO를 설정하고 무한 루프에 들어가므로,
RPi.GPIO·Adafruit_AMG88xx를 스텁으로 바꾸고 스크립트 파일을 exec로 실행한다.
"""
import contextlib
import io
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def gpio(monkeypatch):
    state = {"outputs": [], "inputs": {}, "cleanup": []}
    module = types.ModuleType("RPi.GPIO")
    module.BCM, module.IN, module.OUT, module.LOW, module.HIGH = "BCM", "IN", "OUT", 0, 1
    module.setmode = module.setup = lambda *a, **k: None
    module.output = lambda pin, value: state["outputs"].append((pin, value))
    module.input = lambda pin: state["inputs"].get(pin, 0)
    module.cleanup = lambda pins=None: state["cleanup"].append(pins)
    rpi = types.ModuleType("RPi")
    rpi.GPIO = module
    monkeypatch.setitem(sys.modules, "RPi", rpi)
    monkeypatch.setitem(sys.modules, "RPi.GPIO", module)
    return state


@pytest.fixture
def run_script():
    def _run(name):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile((ROOT / name).read_text(encoding="utf-8"), str(ROOT / name), "exec"),
                 {"__name__": "__main__"})
        return out.getvalue()

    return _run
