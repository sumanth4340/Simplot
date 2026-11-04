"""Vision capture driver: run inbox legs, verify, collect PNGs.

Batch = [(stem, lines, capture_as_or_None)]. Per leg: write inbox,
poll outbox (120s), require ok + all lines ok, snapshot recorded,
PNG size-gated (>8KB) and copied when capture_as is set. Aborts on
first failure with a loud report. Refuses to start when another
driver has pending work.

BATCH below covers vis16-20 (stage/clear + 3 legs each). Extend by
appending; rerun. PNGs land in finetune/images/visNN.png.

Usage:
  python action-reasoner/capture_vis.py [--dry-run]
"""
import argparse
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BRIDGE = ROOT.parent / "action-reasoner-bridge"
IMG_DIR = ROOT / "finetune" / "images"
POLL_TIMEOUT = 120
PNG_MIN_BYTES = 8000

# (stem, lines, capture_as, settle_secs after ok)
# NOTE: sim.step is broken live (World physics context None; 2 samples) —
# settle under sim.play instead. Plans recorded without step lines.
# NOTE 2: one transport op per leg — same-batch timeline reads lag
# (stop-then-play in one batch reads stale "already playing").
# NOTE 3: NEVER delete /World/PhysicsScene mid-session — it orphans the
# physics backend views (all Dynamic* creates fail after); only a
# scene.open recovers. Keep the scene across all capture tasks.
BATCH = [
    # Batch 2: vis21-25 (batch 1 captured; its vis16_c scene-delete
    # must never rerun — see NOTE 3).
    ("vis21_a", [
        "scene.save path=stages/vis21_empty.usd",
    ], "vis21.png"),
    ("vis22_a", [
        "create.objects.cone pos=1,0,0.5 color=1.0,0.5,0.0 name=vbeacon",
    ], "vis22.png"),
    ("vis22_b", [
        "sensor.create.rtx_lidar path=/World/vlidar2",
        "sim.play",
    ], None, 2),
    ("vis22_c", [
        "sim.stop",
        "scene.delete.prim target=/World/vbeacon",
        "scene.delete.prim target=/World/vlidar2",
    ], None),
    ("vis23_a", [
        "create.objects.cuboid pos=0,0,0.25 size=0.6 color=0.6,0.4,0.2 name=vpallet",
        "create.objects.cuboid pos=0,0,0.8 size=0.4 color=0.8,0.6,0.2 name=vtines",
    ], "vis23.png"),
    ("vis23_b", [
        "joint.create.joint joint_type=fixed from_prim=/World/vpallet to_prim=/World/vtines",
    ], None),
    ("vis23_c", [
        "scene.delete.prim target=/World/Joints/vpallet_to_vtines",
        "scene.delete.prim target=/World/vpallet",
        "scene.delete.prim target=/World/vtines",
    ], None),
    ("vis24_a", [
        "create.objects.cuboid pos=0,0,0.5 size=0.6 name=vwob0",
        "create.objects.cuboid pos=0.1,0,1.1 size=0.6 name=vwob1",
    ], "vis24.png"),
    ("vis24_b", ["sim.play"], None, 2),
    ("vis24_c", ["sim.pause"], None),
    ("vis24_d", [
        "sim.stop",
        "scene.delete.prim target=/World/vwob0",
        "scene.delete.prim target=/World/vwob1",
    ], None),
    ("vis25_a", [
        "create.objects.cylinder pos=-1,0,0.5 color=1.0,0.3,0.1 name=vbarrel",
    ], "vis25.png"),
    ("vis25_b", [
        "robot.clone target=vbarrel count=2",
    ], None),
    ("vis25_c", [
        "scene.delete.prim target=/World/vbarrel",
        "scene.delete.prim target=/World/vbarrel_2",
        "scene.delete.prim target=/World/vbarrel_3",
    ], None),
]


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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--from", dest="from_stem", default=None)
    args = parser.parse_args(argv)
    pending = _pending()
    if pending:
        print(f"REFUSE: inbox busy ({pending}); another driver active?")
        return 2
    batch = BATCH
    if args.from_stem:
        stems = [e[0] for e in BATCH]
        batch = BATCH[stems.index(args.from_stem):]
    fails = 0
    for entry in batch:
        stem, lines, capture_as = entry[:3]
        settle = entry[3] if len(entry) > 3 else 0
        if args.dry_run:
            print(f"would run {stem}: {len(lines)} lines"
                  + (f" -> {capture_as}" if capture_as else "")
                  + (f" settle={settle}s" if settle else ""))
            continue
        result, err = run_leg(stem, lines)
        if result is None:
            print(f"FAIL {stem}: {err}")
            return 1
        bad = [r for r in result.get("results", [])
               if not r.get("ok")]
        if not result.get("ok") or bad:
            print(f"FAIL {stem}: ok={result.get('ok')} "
                  f"bad={[ (b.get('key'), b.get('msg')) for b in bad][:3]}")
            return 1
        if settle:
            time.sleep(settle)
            msg_suffix = f" settle={settle}s"
        else:
            msg_suffix = ""
        msg = f"ok {stem}: {len(lines)} lines" + msg_suffix
        if capture_as:
            png = BRIDGE / "outbox" / f"{Path(stem).stem}.png"
            if not png.is_file() or png.stat().st_size < PNG_MIN_BYTES:
                have = png.stat().st_size if png.is_file() else -1
                print(f"FAIL {stem}: shot missing/small ({have} bytes)")
                return 1
            IMG_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(png, IMG_DIR / capture_as)
            msg += f" shot {png.stat().st_size}B -> {capture_as}"
        print(msg, flush=True)
    print(f"batch done: {len(BATCH)} legs, fails={fails}")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
