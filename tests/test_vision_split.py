"""Tests for the vision eval split. Run: python tests/test_vision_split.py"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arvs_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


train = _load("train_glimmer", ROOT / "modal" / "train_glimmer.py")
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def test_split_holds_first_rows_out():
    rows = [{"id": i} for i in range(15)]
    train_rows, eval_rows = train.split_vision_eval(rows)
    assert [r["id"] for r in eval_rows] == [0, 1], eval_rows
    assert len(train_rows) == 13 and len(eval_rows) == 2
    assert {r["id"] for r in train_rows} | {0, 1} == set(range(15))


def test_split_stable_under_append():
    before = train.split_vision_eval([{"id": i} for i in range(15)])[1]
    after = train.split_vision_eval([{"id": i} for i in range(50)])[1]
    assert before == after, (before, after)


def test_split_tiny_keeps_all_in_train():
    train_rows, eval_rows = train.split_vision_eval([{"id": 0}])
    assert len(train_rows) == 1 and eval_rows == []


def test_trace_files_all_present():
    for name in train.TRACE_FILES:
        assert (ROOT / "finetune" / name).is_file(), f"missing {name}"


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
