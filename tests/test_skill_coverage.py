"""Tests for the skill<->action coverage map. Run: python tests/test_skill_coverage.py"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arcv_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


protocol = _load("protocol", EXT_PY / "protocol.py")
handlers = _load("handlers", EXT_PY / "handlers.py")
build_coverage = _load("build_skill_coverage", ROOT / "build_skill_coverage.py")
catalog = protocol.load_catalog(ROOT / "actions_compact.json")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _trace_lines():
    total = 0
    for name in build_coverage.TRACE_FILES:
        path = ROOT / "finetune" / name
        assert path.is_file(), f"missing {path}"
        total += sum(1 for line in path.read_text(encoding="utf-8").splitlines()
                     if line.strip())
    return total


def test_coverage_counts_match_trace_files():
    coverage, stats = build_coverage.generate(None)
    assert coverage["meta"]["traces"] == stats["traces"] == _trace_lines()
    assert coverage["meta"]["compact_actions"] == len(catalog)
    assert set(coverage["by_action"]) == set(catalog)


def test_no_trace_key_outside_compact():
    coverage, stats = build_coverage.generate(None)
    assert coverage["meta"]["unknown_keys"] == {}, stats["unknown_keys"]
    assert stats["unknown_keys"] == {}


def test_handled_actions_all_in_compact():
    missing = [k for k in handlers.HANDLED_ACTIONS if k not in catalog]
    assert missing == [], f"silently dropped from prompt: {missing}"


def test_gaps_consistent_with_counts():
    coverage, _ = build_coverage.generate(None)
    by_action = coverage["by_action"]
    expect_handled = sorted(k for k, v in by_action.items()
                            if v["handled"] and v["traces"] == 0)
    expect_available = sorted(k for k, v in by_action.items()
                              if v["available"] and v["traces"] == 0)
    assert coverage["gaps"]["handled_undrilled"] == expect_handled
    assert coverage["gaps"]["available_undrilled"] == expect_available


def test_every_drill_group_has_actions():
    coverage, _ = build_coverage.generate(None)
    assert coverage["by_drill"], "no drill groups found"
    for drill, entry in coverage["by_drill"].items():
        assert entry["traces"] > 0, drill
        assert entry["actions"] or entry.get("dispatch"), \
            f"drill {drill} covers nothing"


def test_write_roundtrip():
    tmp = Path(tempfile.mkdtemp(prefix="ar_cov_"))
    out = tmp / "skills_action_coverage.json"
    coverage, _ = build_coverage.generate(out)
    assert out.is_file()
    assert json.loads(out.read_text(encoding="utf-8")) == coverage


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
