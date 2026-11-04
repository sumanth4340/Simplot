"""Tests for guided-decoding support. Run: python tests/test_guided.py"""
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"
DATA = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "data"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"argd_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker", EXT_PY / "thinker.py")
protocol = _load("protocol", EXT_PY / "protocol.py")
handlers = _load("handlers", EXT_PY / "handlers.py")
catalog = protocol.load_catalog(ROOT / "actions_compact.json")
build_traces = _load("build_traces", ROOT / "build_traces.py")
build_drills = _load("build_drill_traces", ROOT / "build_drill_traces.py")
build_dispatch = _load("build_dispatch_traces", ROOT / "build_dispatch_traces.py")
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _pattern():
    text = (DATA / "guided_action_regex.txt").read_text(encoding="utf-8").strip()
    return re.compile(text)


def test_artifact_loads_and_compiles():
    assert thinker.load_guided_regex(), "run build_guided_regex.py"
    assert thinker.load_guided_regex() == (
        DATA / "guided_action_regex.txt").read_text(encoding="utf-8").strip()


def test_accepts_valid_lines():
    pat = _pattern()
    assert pat.fullmatch("create.objects.cuboid size=1 pos=0,0,2")
    assert pat.fullmatch("sim.play")
    assert pat.fullmatch("# a comment stays")
    assert pat.fullmatch("DONE")
    assert pat.fullmatch("DEPLOY agent=sense needs=stage")
    assert pat.fullmatch("STEP n=1 agent=sense do=read-stage")
    assert pat.fullmatch("PARALLEL agents=sense+stage")
    assert pat.fullmatch("COWORK agents=articulation+physics")
    multi = ("# plan\ncreate.objects.plane size=20\n"
             "create.objects.cuboid size=1 pos=0,0,2 color=0.2,0.4,0.9\n")
    assert pat.fullmatch(multi)


def test_rejects_prose():
    pat = _pattern()
    assert not pat.fullmatch("I will make a cube now")
    assert not pat.fullmatch("1. create.objects.cuboid size=1")
    assert not pat.fullmatch("```\nsim.play\n```")
    assert not pat.fullmatch("sim.play\nHere is your scene!")
    assert not pat.fullmatch("")


def test_covers_every_catalog_key():
    pat = _pattern()
    for key in catalog:
        assert pat.fullmatch(key), key
    for key in handlers.HANDLED_ACTIONS:
        assert pat.fullmatch(f"{key} target=/World/x value=1"), key


def test_covers_training_distribution():
    pat = _pattern()
    tmp = Path(tempfile.mkdtemp(prefix="ar_guided_"))
    build_traces.generate(tmp / "mock")
    build_drills.generate(tmp / "drills")
    build_dispatch.generate(tmp / "dsp")
    n = 0
    for name in ("mock/traces_mock.jsonl", "drills/traces_drills.jsonl",
                 "dsp/traces_dispatch.jsonl"):
        for line in (tmp / name).read_text(encoding="utf-8").splitlines():
            content = json.loads(line)["messages"][2]["content"]
            assert pat.fullmatch(content), content[:120]
            n += 1
    for committed in ("traces_live.jsonl",):
        path = ROOT / "finetune" / committed
        assert path.is_file(), f"run the {committed} builder"
        for line in path.read_text(encoding="utf-8").splitlines():
            content = json.loads(line)["messages"][2]["content"]
            assert pat.fullmatch(content), content[:120]
            n += 1
    assert n > 400, n


def test_request_body_default_unchanged():
    body = thinker._request_body("m", [{"role": "user"}], 128)
    assert body == {"model": "m", "messages": [{"role": "user"}],
                    "temperature": 0.2, "max_tokens": 128}
    assert "guided_regex" not in body
    stream = thinker._request_body("m", [], 64, stream=True)
    assert stream["stream"] is True and "guided_regex" not in stream
    guided = thinker._request_body("m", [], 64, guided_regex="X+")
    assert guided["guided_regex"] == "X+"


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
