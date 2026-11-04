"""Convert worked live history into SFT traces (backend "live").

Mines two sources, same chat shape as the other builders:
  * GUI think+run pairs from ~/action-reasoner-traces/traces.jsonl —
    real stage snapshots with verified-ok action lines.
  * Bridge legs (action-reasoner-bridge/done/*.txt + outbox results) —
    task from the cmd file's # header, snapshot + ok + screenshot
    from the outbox result JSON.

Only all-ok executions convert; every line re-validates against the
current catalog, and every record passes trace_schema. Live snapshots
are truncated to SNAP_MAX chars so records stay trainable; screenshot
paths are carried in meta.image_paths for the future vision set
(messages stay text-only, images: 0).

Outputs (default: action-reasoner/finetune/):
  traces_live.jsonl - one {"messages": [...], "meta": {...}} per run.

Usage:
  python action-reasoner/build_live_traces.py [--out DIR]
"""
import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXT_PY = (ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim"
          / "action" / "reasoner" / "executor")
LIVE_LOG = Path.home() / "action-reasoner-traces" / "traces.jsonl"
BRIDGE = ROOT.parent / "action-reasoner-bridge"
SNAP_MAX = 1500
_DESTRUCTIVE = {"delete", "deletes", "remove", "removes", "clear",
                "destroy", "demolish"}


def _load(name):
    spec = importlib.util.spec_from_file_location(f"arlive_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker")
protocol = _load("protocol")
handlers = _load("handlers")

_spec_ts = importlib.util.spec_from_file_location(
    "ar_trace_schema", ROOT / "trace_schema.py")
trace_schema = importlib.util.module_from_spec(_spec_ts)
sys.modules["ar_trace_schema"] = trace_schema
_spec_ts.loader.exec_module(trace_schema)


def _trunc(snapshot: str) -> tuple:
    if len(snapshot) <= SNAP_MAX:
        return snapshot, False
    return snapshot[:SNAP_MAX] + "\n...(snapshot truncated)", True


def _record(task, snapshot, snap_label, lines, keys, skills, source,
            image_paths, truncated):
    skills_entries = skills
    names = [s.get("skill") or s.get("name") for s in skills_entries]
    return {
        "messages": [
            {"role": "system",
             "content": thinker.build_system_prompt(SIGNATURES, skills_entries)},
            {"role": "user",
             "content": thinker.build_user_prompt(task, snapshot)},
            {"role": "assistant", "content": "\n".join(lines)},
        ],
        "meta": {
            "task": task,
            "backend": "live",
            "source": source,
            "skills": names,
            "validated": True,
            "images": 0,
            "snapshot": snap_label + ("+truncated" if truncated else ""),
            "actions": keys,
            "image_paths": image_paths,
        },
    }


def _validate_lines(lines, catalog, stats, where):
    keys = []
    for key, raw, lineno in protocol.parse_batch("\n".join(lines)):
        try:
            action = protocol.validate(key, raw, catalog, lineno=lineno)
        except (protocol.ValidationError, protocol.ProtocolError) as e:
            stats["line_rejected"] += 1
            stats["reject_samples"].append(f"{where}: {key}: {e}"[:160])
            return None
        keys.append(action.key)
    if not keys:
        return None
    return keys


def generate(out_dir: Path, live_log=None, bridge_dir=None) -> dict:
    live_log = Path(live_log or LIVE_LOG)
    bridge_dir = Path(bridge_dir or BRIDGE)
    catalog = protocol.load_catalog(ROOT / "actions_compact.json")
    routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))
    global SIGNATURES
    SIGNATURES = [protocol.help_line(k, catalog[k])
                  for k in handlers.HANDLED_ACTIONS if k in catalog]
    stats = {"think_runs": 0, "bridge_runs": 0, "written": 0,
             "unpaired": 0, "not_ok": 0, "line_rejected": 0,
             "intent_mismatch": 0, "dupes": 0, "schema_fail": 0,
             "truncated": 0, "reject_samples": [], "groups": Counter(),
             "skills": Counter()}
    if not live_log.is_file():
        print(f"no live log at {live_log}")
        return stats
    events = [json.loads(line) for line in
              live_log.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    thinks = [e for e in events if e.get("event") == "think" and e.get("task")]
    runs = [e for e in events if e.get("event") == "run" and e.get("lines")]
    seen = set()
    out_dir.mkdir(parents=True, exist_ok=True)

    def emit(record, task, keys, names):
        schema_errs = trace_schema.validate_record(record)
        if schema_errs:
            stats["schema_fail"] += 1
            return False
        digest = (task, record["messages"][2]["content"])
        if digest in seen:
            stats["dupes"] += 1
            return False
        seen.add(digest)
        f.write(json.dumps(record) + "\n")
        stats["written"] += 1
        for key in keys:
            stats["groups"][catalog[key].get("group")] += 1
        for name in names:
            stats["skills"][name] += 1
        return True

    with open(out_dir / "traces_live.jsonl", "w", encoding="utf-8") as f:
        for run in runs:
            results = run.get("results") or []
            if not results or not all(r.get("ok") for r in results):
                stats["not_ok"] += 1
                continue
            want = [ln.strip() for ln in run["lines"] if ln.strip()]
            best = None
            for th in thinks:
                planned = [ln.strip() for ln in
                           (th.get("actions") or "").splitlines() if ln.strip()]
                if planned == want and (best is None or th.get("ts", "") > best.get("ts", "")):
                    best = th
            if best is None:
                stats["unpaired"] += 1
                continue
            if any("no keywords matched" in (n or "") for n in (best.get("notes") or [])):
                stats["intent_mismatch"] += 1
                continue
            task_words = set(re.findall(r"[a-z0-9]+", (best.get("task") or "").lower()))
            if task_words & _DESTRUCTIVE and "scene.delete.prim" not in [
                    ln.split(None, 1)[0] for ln in want if ln.split()]:
                stats["intent_mismatch"] += 1
                continue
            stats["think_runs"] += 1
            keys = _validate_lines(want, catalog, stats, f"run@{run.get('ts')}")
            if keys is None:
                continue
            task = best["task"]
            skills = thinker.select_skills(task, routing)
            snap, trunc = _trunc(best.get("snapshot") or "")
            stats["truncated"] += trunc
            shots = [p for p in (best.get("images") or []) if p and Path(p).is_file()]
            emit(_record(task, snap, "live-gui", want, keys, skills,
                         "think-run", shots, trunc), task, keys,
                 [s.get("skill") or s.get("name") for s in skills])
        for ev in events:
            if ev.get("event") != "bridge_run" or not ev.get("lines"):
                continue
            results = ev.get("results") or []
            if not results or not all(r.get("ok") for r in results):
                stats["not_ok"] += 1
                continue
            cmd = ev.get("cmd") or ""
            cmd_file = bridge_dir / "done" / cmd
            if not cmd or not cmd_file.is_file():
                stats["unpaired"] += 1
                continue
            cmd_lines = [ln.strip() for ln in
                         cmd_file.read_text(encoding="utf-8", errors="replace").splitlines()]
            task = next((ln[1:].strip() for ln in cmd_lines if ln.startswith("#")), "")
            if not task:
                stats["unpaired"] += 1
                continue
            stem = Path(cmd).stem
            res_file = bridge_dir / "outbox" / f"{stem}.result.json"
            snap, shot = "", None
            if res_file.is_file():
                try:
                    res = json.loads(res_file.read_text(encoding="utf-8"))
                except ValueError:
                    res = {}
                if not res.get("ok", True):
                    stats["not_ok"] += 1
                    continue
                snap = res.get("snapshot") or ""
                shot = bridge_dir / "outbox" / f"{stem}.png"
            stats["bridge_runs"] += 1
            want = [ln for ln in cmd_lines if ln and not ln.startswith("#")]
            keys = _validate_lines(want, catalog, stats, f"bridge:{cmd}")
            if keys is None:
                continue
            skills = thinker.select_skills(task, routing)
            snap, trunc = _trunc(snap)
            stats["truncated"] += trunc
            shots = [str(shot)] if shot and shot.is_file() else []
            emit(_record(task, snap, "live-bridge", want, keys, skills,
                         "bridge", shots, trunc), task, keys,
                 [s.get("skill") or s.get("name") for s in skills])
    return stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert live history to SFT traces")
    parser.add_argument("--out", default=str(ROOT / "finetune"),
                        help="output directory")
    args = parser.parse_args(argv)
    stats = generate(Path(args.out))
    print(f"think-runs: {stats['think_runs']} bridge-runs: {stats['bridge_runs']} "
          f"written: {stats['written']}")
    print(f"unpaired: {stats['unpaired']} not_ok: {stats['not_ok']} "
          f"line_rejected: {stats['line_rejected']} "
          f"intent_mismatch: {stats['intent_mismatch']} dupes: {stats['dupes']} "
          f"schema_fail: {stats['schema_fail']} truncated: {stats['truncated']}")
    for sample in stats["reject_samples"][:8]:
        print(f"  REJECTED :: {sample}")
    print(f"action groups in traces: {dict(stats['groups'])}")
    print(f"out: {args.out}")
    return 0 if not stats["schema_fail"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
