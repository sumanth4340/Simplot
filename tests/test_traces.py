"""Tests for fine-tune data. Run: python tests/test_traces.py"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"artr_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


protocol = _load("protocol", EXT_PY / "protocol.py")
build_traces = _load("build_traces", ROOT / "build_traces.py")
catalog = protocol.load_catalog(ROOT / "actions_compact.json")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _generated():
    tmp = Path(tempfile.mkdtemp(prefix="ar_traces_"))
    stats = build_traces.generate(tmp)
    return tmp, stats


def test_curation_drops_only_dead_actions():
    trainable, excluded = build_traces.curate(catalog)
    assert len(trainable) + len(excluded) == len(catalog)
    assert all(v.get("available") for v in trainable.values())
    assert all(not v.get("available") for v in excluded.values())
    assert len(excluded) == 26, f"expected 26 dead, got {len(excluded)}"


def test_traces_are_valid_chat_records():
    tmp, stats = _generated()
    assert stats["skipped"] == [], stats["skipped"]
    assert stats["tasks"] == len(build_traces.TASKS), stats
    lines = (tmp / "traces_mock.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == stats["tasks"] and lines
    for line in lines:
        record = json.loads(line)
        assert [m["role"] for m in record["messages"]] == [
            "system", "user", "assistant"], record["meta"]
        assert record["meta"]["validated"] is True
        assert record["meta"]["backend"] == "mock"
        batch = protocol.parse_batch(record["messages"][2]["content"])
        assert batch, f"empty plan for {record['meta']['task']!r}"
        for key, raw, lineno in batch:
            action = protocol.validate(key, raw, catalog, lineno=lineno)
            assert catalog[action.key].get("available"), f"dead in traces: {key}"


def test_finetune_artifact_matches_curation():
    tmp, stats = _generated()
    artifact = json.loads((tmp / "actions_finetune.json").read_text(encoding="utf-8"))
    assert len(artifact) == stats["trainable"] == 169, len(artifact)
    assert set(artifact) | set(stats["excluded"]) == set(catalog)
    assert not (set(artifact) & set(stats["excluded"]))


def test_committed_finetune_dir_exists():
    finetune = ROOT / "finetune"
    assert (finetune / "traces_mock.jsonl").is_file(), "run build_traces.py"
    assert (finetune / "actions_finetune.json").is_file(), "run build_traces.py"


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
