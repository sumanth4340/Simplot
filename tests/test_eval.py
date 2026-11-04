"""Tests for the eval scorer. Run: python tests/test_eval.py"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arev_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


protocol = _load("protocol", EXT_PY / "protocol.py")
thinker = _load("thinker", EXT_PY / "thinker.py")
score = _load("score", ROOT / "eval" / "score.py")
catalog = protocol.load_catalog(ROOT / "actions_compact.json")
routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def test_action_perfect_scores_one():
    out = score.score_action_output(
        "# plan\ncreate.objects.plane size=20\nsim.play\n",
        catalog, "pyapi", ["pyapi", "stage"])
    assert out == {"total": 2, "valid": 2, "valid_rate": 1.0,
                   "skill_hit": True, "prose": False, "errors": []}, out


def test_action_prose_and_bad_lines_score_down():
    out = score.score_action_output(
        "Here you go:\ncreate.objects.plane size=20\n"
        "create.objects.cuboid size=oops\n",
        catalog, "pyapi", ["stage"])
    assert out["total"] == 2 and out["valid"] == 1, out
    assert out["valid_rate"] == 0.5 and out["prose"] is True, out
    assert out["skill_hit"] is False and len(out["errors"]) == 1, out


def test_action_empty_scores_zero():
    out = score.score_action_output("# nothing\n", catalog, "stage", ["stage"])
    assert out["total"] == 0 and out["valid_rate"] == 0.0, out


def test_action_malformed_line_scores_invalid_not_crash():
    # First adapter grade died here: a trailing bare token raised
    # inside parse_batch and killed the whole suite.
    out = score.score_action_output(
        "create.objects.plane size=20\n"
        "create.objects.cuboid size=1 pos=0,0,2 0.0,\n",
        catalog, "stage", ["stage"])
    assert out["total"] == 2 and out["valid"] == 1, out
    assert out["valid_rate"] == 0.5 and len(out["errors"]) == 1, out


def test_dispatch_scores_acceptance():
    good = score.score_dispatch_output(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n")
    assert good["accepted"] is True and good["deploys"] == 1, good
    assert good["agents"] == ["sense"], good
    bad = score.score_dispatch_output("I will deploy sense now\n")
    assert bad["accepted"] is False and bad["error"], bad


def test_from_file_scores_saved_generations():
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="ar_evalfrom_"))
    gens = tmp / "gens.jsonl"
    gens.write_text(
        json.dumps({"id": "EA1",
                    "output": "create.objects.plane size=20\nsim.play\n"})
        + "\n"
        + json.dumps({"id": "ED1", "output": "prose, not a plan\n"}) + "\n",
        encoding="utf-8")
    run_eval = _load("run_eval", ROOT / "eval" / "run_eval.py")
    rc = run_eval.main(["--from", str(gens), "--out", str(tmp / "r.json")])
    assert rc == 0
    report = json.loads((tmp / "r.json").read_text(encoding="utf-8"))
    assert report["backend"].startswith("file:"), report["backend"]
    by_id = {e["id"]: e for e in report["tasks"]}
    assert by_id["EA1"]["valid_rate"] == 1.0, by_id["EA1"]
    assert by_id["ED1"]["accepted"] is False, by_id["ED1"]
    assert by_id["EA2"]["supported"] is False  # no saved output


def test_mock_suite_completes_with_pinned_hits():
    report = score.run_suite(
        lambda task: thinker.mock_plan(task["task"], task["snapshot"])[0]
        if task["kind"] == "action" else None,
        catalog, routing)
    assert len(report["tasks"]) == 12, report["summary"]
    summary = report["summary"]
    assert summary["action_valid_rate"] == 1.0, summary
    assert summary["dispatch_tasks"] == 0 and summary["unsupported"] == 4
    assert summary["skill_hit_rate"] == 1.0, summary


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
