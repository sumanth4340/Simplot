"""DWA proof-replay driver: re-drive demo_proof.txt through the bridge.

Reads the planner proof (nav/demo_proof.txt: one v/w -> L/R wheel
command per step), gates the mission on nav/preflight with the
declared start/goal, then fires one inbox leg per proof step:
two robot.set.joint_drive target_velocity lines + a settle so the
car actually rolls. Aborts loud on the first failure (gate FAIL,
bridge timeout, or any line not ok). Mirrors capture_vis.py bridge
mechanics (refuse-if-busy, outbox poll, --dry-run, --from resume).

Joint targets are required CLI args: the DWA car's joint names live
in the saved stage, not in this repo — read them from a Snapshot
registry dump, never guess. Closed-loop pose feedback (snapshot ->
replan) is future work; this replay is open-loop by design and says
so on every run.

Usage:
  python action-reasoner/nav/drive_mission.py --left <joint> --right <joint>
  python action-reasoner/nav/drive_mission.py --left a --right b --dry-run
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIDGE = ROOT.parent / "action-reasoner-bridge"
PROOF = Path(__file__).resolve().parent / "demo_proof.txt"
POLL_TIMEOUT = 120

sys.path.insert(0, str(ROOT / "nav"))
import dwa  # noqa: E402
import preflight  # noqa: E402

# Grounded mission constants (see module docstring for provenance).
STAGE_DEFAULT = "C:/isaacsim/stages/dwa_final.usd"
GOAL_DEFAULT = (-2.2, 2.4)  # proof end (-1.85,2.09) sits 0.47 m off it
START_DEFAULT = (1.807, 0.0, -0.0593)  # saved-start pose, radians
STEP_SECS_DEFAULT = 1.0  # live legs: 0.53 m per 1 s leg

_STEP_RE = re.compile(
    r"^step (\d+): v=([+-]?[\d.]+) w=([+-]?[\d.]+) "
    r"-> L=([+-]?\d+) R=([+-]?\d+) deg/s leg=(\d+) r=([\d.]+)")


def parse_proof_steps(text: str) -> list:
    """Proof text -> [(v, w, L, R, leg, r)] in step order.

    Raises ValueError on empty/garbled input so a truncated proof
    never drives silently.
    """
    steps = []
    for line in (text or "").splitlines():
        m = _STEP_RE.match(line.strip())
        if m:
            n, v, w, L, R, leg, r = m.groups()
            steps.append((float(v), float(w), int(L), int(R),
                          int(leg), float(r)))
    if not steps:
        raise ValueError("no proof steps parsed (file truncated?)")
    return steps


def build_step_lines(L: int, R: int, left: str, right: str) -> list:
    """One proof step -> two joint_drive velocity lines (deg/s)."""
    return [
        f"robot.set.joint_drive target={left} target_velocity={L}",
        f"robot.set.joint_drive target={right} target_velocity={R}",
    ]


def gate_mission(start, goal, cfg) -> tuple:
    """Preflight gate -> (go: bool, report lines). Veto = no bridge."""
    state = [start[0], start[1], start[2], 0.0, 0.0]
    checks = preflight.preflight(state, goal, [], cfg)
    report = preflight.format_report(checks)
    return preflight.verdict(checks) != "fail", report


def _pending():
    try:
        return [p.name for p in (BRIDGE / "inbox").iterdir()
                if p.is_file() and p.suffix == ".txt"]
    except OSError:
        return ["<inbox unreadable>"]


def run_leg(stem, lines):
    inbox = BRIDGE / "inbox" / f"{stem}.txt"
    res = BRIDGE / "outbox" / f"{stem}.result.json"
    if res.exists():
        res.unlink()
    inbox.write_text("# " + stem + "\n" + "\n".join(lines) + "\n",
                     encoding="utf-8")
    waited = 0
    while waited < POLL_TIMEOUT:
        if res.exists():
            break
        time.sleep(3)
        waited += 3
    if not res.exists():
        return None, f"TIMEOUT after {POLL_TIMEOUT}s"
    try:
        return json.loads(res.read_text(encoding="utf-8")), ""
    except ValueError as exc:
        return None, f"bad result json: {exc}"


def _fail(result):
    bad = [r for r in result.get("results", []) if not r.get("ok")]
    if not result.get("ok") or bad:
        shown = [(b.get("key"), b.get("msg")) for b in bad][:3]
        return f"ok={result.get('ok')} bad={shown}"
    return ""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True,
                        help="left wheel joint target (from Snapshot)")
    parser.add_argument("--right", required=True,
                        help="right wheel joint target (from Snapshot)")
    parser.add_argument("--stage", default=STAGE_DEFAULT)
    parser.add_argument("--goal", default=",".join(
        str(v) for v in GOAL_DEFAULT))
    parser.add_argument("--start", default=",".join(
        str(v) for v in START_DEFAULT))
    parser.add_argument("--step-secs", type=float,
                        default=STEP_SECS_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--from", dest="from_stem", default=None)
    args = parser.parse_args(argv)
    try:
        steps = parse_proof_steps(PROOF.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"REFUSE: cannot load proof: {exc}")
        return 2
    goal = tuple(float(v) for v in args.goal.split(","))
    start = tuple(float(v) for v in args.start.split(","))
    go, report = gate_mission(start, goal, dwa.DWAConfig.live())
    print("\n".join(report))
    if not go:
        print("REFUSE: mission vetoed by preflight (no bridge writes)")
        return 1
    legs = [(f"dwa_open", [f"scene.open path={args.stage}", "sim.play"])]
    for i, (_v, _w, L, R, _leg, _r) in enumerate(steps):
        legs.append((f"dwa_{i:02d}",
                     build_step_lines(L, R, args.left, args.right)))
    legs.append((f"dwa_zero",
                 build_step_lines(0, 0, args.left, args.right)))
    legs.append(("dwa_pause", ["sim.pause"]))
    legs.append(("dwa_stop", ["sim.stop"]))
    if args.from_stem:
        stems = [s for s, _ in legs]
        legs = legs[stems.index(args.from_stem):]
    print(f"open-loop replay: {len(steps)} proof steps "
          f"(closed-loop feedback is future work)")
    if args.dry_run:
        for stem, lines in legs:
            print(f"would run {stem}: {len(lines)} lines")
        return 0
    pending = _pending()
    if pending:
        print(f"REFUSE: inbox busy ({pending}); another driver active?")
        return 2
    for stem, lines in legs:
        result, err = run_leg(stem, lines)
        if result is None:
            print(f"FAIL {stem}: {err}")
            return 1
        if problem := _fail(result):
            print(f"FAIL {stem}: {problem}")
            return 1
        print(f"ok {stem}: {len(lines)} lines", flush=True)
        if stem.startswith("dwa_") and stem not in (
                "dwa_open", "dwa_zero", "dwa_pause", "dwa_stop"):
            time.sleep(args.step_secs)
    print(f"mission done: {len(legs)} legs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
