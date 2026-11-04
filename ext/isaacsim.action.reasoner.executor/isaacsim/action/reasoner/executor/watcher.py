"""Sense watchdog: always-on stage tracker, speaks only on delta.

The workspace-sense agent's always-on half. This module is CODE, not the
LLM: it diffs compact stage snapshots and emits ``event.*`` action lines
only when something actually changed. Quiet ticks return [].

Two triggers (wired in window.py):
  1. action boundary — snapshot before/after every executed batch, so
     everything the AI itself did is tracked;
  2. idle poll — the bridge loop observes once per tick, so external
     edits (a dragged prim, another writer) are caught too.

Screenshot diffing is deliberately NOT the tracker: a camera has blind
spots (occlusion, off-frame prims, exact deltas). This diffs USD state —
prims, poses, physics flags, joints, timeline — so every pinpoint change
reports where it happened and what changed. Viewport captures stay an
on-demand verifier for look-only questions (materials, lighting, render
errors), owned by observer.py.

Motion gating: while the timeline plays, sim poses change every frame.
The idle poll skips motion diffs while playing (structural changes and
timeline transitions still report) so a falling ball does not spam one
event per tick; the action-boundary diff always reports full motion.
``live`` sim poses come from RigidPrim tensors when available
(playing, or rested with clock>0); otherwise diffs use authored pose.

All Kit/USD imports are guarded so the diff core imports and unit-tests
outside Isaac Sim; capture_compact() returns None there (caller stays
quiet).
"""
from __future__ import annotations

import hashlib
import json

POS_QUANT = 0.001  # hash grid (m): sub-mm jitter stays quiet
POS_EPS_DEFAULT = 0.005  # moved events need >= 5 mm displacement
SIM_EPS_DEFAULT = 0.02  # sim-pose moves need >= 2 cm (tensor noise)
MASS_EPS = 1e-6
MAX_EVENTS = 50  # bigger diffs collapse to one resync line


def _q(x, grid=POS_QUANT):
    """Quantize a float onto the hash grid; None-safe."""
    try:
        return round(round(float(x) / grid) * grid, 6)
    except (TypeError, ValueError):
        return None


def _vec_eq(a, b, eps):
    if a is None or b is None:
        return a is None and b is None
    try:
        return all(abs(float(x) - float(y)) <= eps for x, y in zip(a, b))
    except (TypeError, ValueError):
        return False


def _vec_delta(a, b):
    d = [float(y) - float(x) for x, y in zip(a, b)]
    dist = sum(v * v for v in d) ** 0.5
    return d, dist


def normalize_snapshot(snap):
    """Canonical comparable form: prims/joints keyed by path, poses quantized."""
    prims = {}
    for rec in snap.get("prims") or []:
        path = rec.get("path")
        if not path:
            continue
        pos = rec.get("pos")
        sim = rec.get("sim")
        prims[path] = {
            "type": rec.get("type"),
            "pos": [_q(v) for v in pos] if pos else None,
            "sim": [_q(v) for v in sim] if sim else None,
            "rigid": rec.get("rigid"),
            "collision": rec.get("collision"),
            "kinematic": rec.get("kinematic"),
            "mass": rec.get("mass"),
        }
    joints = {}
    for rec in snap.get("joints") or []:
        path = rec.get("path")
        if path:
            joints[path] = {
                "type": rec.get("type"),
                "body0": sorted(rec.get("body0") or []),
                "body1": sorted(rec.get("body1") or []),
            }
    tl = snap.get("timeline") or {}
    return {
        "prims": prims,
        "joints": joints,
        "timeline": {"playing": tl.get("playing")},
        "physics_scene": snap.get("physics_scene"),
    }


def snapshot_hash(snap) -> str:
    """Stable sha256 over the normalized snapshot (order-independent)."""
    canon = normalize_snapshot(snap)
    blob = json.dumps(canon, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _fmt_num(x, n=3):
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return "?"


def diff_snapshots(before, after, pos_eps=POS_EPS_DEFAULT,
                   sim_eps=SIM_EPS_DEFAULT, include_motion=True):
    """Diff two compact snapshots -> list of event.* action lines.

    Returns [] when nothing meaningful changed. ``include_motion=False``
    skips pose diffs (idle poll while playing); structure, flags and
    timeline transitions still report.
    """
    if before is None or after is None:
        return []
    b = normalize_snapshot(before)
    a = normalize_snapshot(after)
    events = []

    b_prims, a_prims = b["prims"], a["prims"]
    for path in sorted(set(a_prims) - set(b_prims)):
        events.append(f"event.stage.prim_added path={path} "
                      f"type={a_prims[path]['type']}")
    for path in sorted(set(b_prims) - set(a_prims)):
        events.append(f"event.stage.prim_removed path={path}")
    for path in sorted(set(b_prims) & set(a_prims)):
        pb, pa = b_prims[path], a_prims[path]
        if pa["type"] != pb["type"]:
            events.append(f"event.stage.retyped path={path} "
                          f"{pb['type']}->{pa['type']}")
        for flag in ("rigid", "collision", "kinematic"):
            if pa[flag] != pb[flag]:
                events.append(f"event.physics.changed path={path} "
                              f"{flag}={pb[flag]}->{pa[flag]}")
        mb, ma = pb["mass"], pa["mass"]
        if mb != ma and not (
                isinstance(mb, (int, float))
                and isinstance(ma, (int, float))
                and abs(mb - ma) <= MASS_EPS):
            events.append(f"event.mass.changed path={path} "
                          f"{_fmt_num(mb, 4)}->{_fmt_num(ma, 4)}")
        if include_motion:
            moved = False
            if pa["sim"] is not None and pb["sim"] is not None:
                if not _vec_eq(pb["sim"], pa["sim"], sim_eps):
                    d, dist = _vec_delta(pb["sim"], pa["sim"])
                    events.append(
                        f"event.pose.moved path={path} "
                        f"dx={_fmt_num(d[0])} dy={_fmt_num(d[1])} "
                        f"dz={_fmt_num(d[2])} dist={_fmt_num(dist)} src=sim")
                    moved = True
            if not moved and pa["pos"] is not None and pb["pos"] is not None:
                if not _vec_eq(pb["pos"], pa["pos"], pos_eps):
                    d, dist = _vec_delta(pb["pos"], pa["pos"])
                    events.append(
                        f"event.pose.moved path={path} "
                        f"dx={_fmt_num(d[0])} dy={_fmt_num(d[1])} "
                        f"dz={_fmt_num(d[2])} dist={_fmt_num(dist)}")

    b_joints, a_joints = b["joints"], a["joints"]
    for path in sorted(set(a_joints) - set(b_joints)):
        events.append(f"event.joint.added path={path} "
                      f"type={a_joints[path]['type']}")
    for path in sorted(set(b_joints) - set(a_joints)):
        events.append(f"event.joint.removed path={path}")
    for path in sorted(set(b_joints) & set(a_joints)):
        if a_joints[path] != b_joints[path]:
            events.append(f"event.joint.changed path={path}")

    bp = b["timeline"].get("playing")
    ap = a["timeline"].get("playing")
    if isinstance(bp, bool) and isinstance(ap, bool) and ap != bp:
        events.append("event.timeline.started" if ap else "event.timeline.stopped")

    if a["physics_scene"] != b["physics_scene"]:
        events.append(f"event.stage.physics_scene "
                      f"{b['physics_scene']}->{a['physics_scene']}")

    if len(events) > MAX_EVENTS:
        events = [f"event.stage.resync before_prims={len(b_prims)} "
                  f"after_prims={len(a_prims)} changes={len(events)}"]
    return events


class Watcher:
    """Holds the baseline snapshot; observe() diffs and adopts."""

    def __init__(self, pos_eps=POS_EPS_DEFAULT, sim_eps=SIM_EPS_DEFAULT):
        self._base = None
        self._pos_eps = pos_eps
        self._sim_eps = sim_eps

    def establish(self, snap) -> None:
        """Adopt a baseline silently (startup; never emits)."""
        if snap is not None:
            self._base = snap

    def observe(self, snap):
        """Diff against baseline, adopt it, return events ([] when quiet).

        First observation establishes the baseline and returns [].
        While playing, motion diffs are skipped to avoid per-tick spam;
        structure, flags and timeline transitions still report.
        """
        if snap is None:
            return []
        if self._base is None:
            self._base = snap
            return []
        base_playing = (self._base.get("timeline") or {}).get("playing")
        now_playing = (snap.get("timeline") or {}).get("playing")
        motion = not (base_playing is True and now_playing is True)
        events = diff_snapshots(self._base, snap, pos_eps=self._pos_eps,
                                sim_eps=self._sim_eps, include_motion=motion)
        self._base = snap
        return events

    def observe_after(self, before, after):
        """Action-boundary diff: full motion diff, then adopt ``after``."""
        if before is None or after is None:
            if after is not None:
                self._base = after
            return []
        events = diff_snapshots(before, after, pos_eps=self._pos_eps,
                                sim_eps=self._sim_eps, include_motion=True)
        self._base = after
        return events

    @property
    def baseline_hash(self):
        return snapshot_hash(self._base) if self._base is not None else None


def capture_compact():
    """Capture a compact snapshot of the live stage, or None.

    None outside Isaac Sim, with no stage, or on capture failure — the
    caller stays quiet. Mirrors sense.py's walk (authored pose via
    XformCache, physics flags, minimal joint records) plus RigidPrim
    sim poses when tensors are available.
    """
    try:
        import omni.usd
        from pxr import Usd, UsdGeom, UsdPhysics
    except Exception:
        return None
    try:
        stage = omni.usd.get_context().get_stage()
    except Exception:
        return None
    if stage is None or not stage:
        return None
    out = {"prims": [], "joints": [], "timeline": {},
           "physics_scene": None}
    try:
        import isaacsim.core.experimental.utils.app as app_utils
        import omni.timeline
        tiface = omni.timeline.get_timeline_interface()
        out["timeline"] = {
            "playing": bool(app_utils.is_playing()),
            "t": round(float(tiface.get_current_time()), 3),
        }
    except Exception:
        out["timeline"] = {"playing": None, "t": None}
    try:
        xcache = UsdGeom.XformCache(Usd.TimeCode.Default())
    except Exception:
        return None
    for prim in stage.Traverse():
        try:
            path = str(prim.GetPath())
            rec = {"path": path, "type": prim.GetTypeName()}
            try:
                t = xcache.GetLocalToWorldTransform(prim).ExtractTranslation()
                rec["pos"] = [round(float(t[0]), 4), round(float(t[1]), 4),
                              round(float(t[2]), 4)]
            except Exception:
                rec["pos"] = None
            try:
                rec["rigid"] = bool(prim.HasAPI(UsdPhysics.RigidBodyAPI))
            except Exception:
                rec["rigid"] = None
            try:
                rec["collision"] = bool(prim.HasAPI(UsdPhysics.CollisionAPI))
            except Exception:
                rec["collision"] = None
            try:
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    rb = UsdPhysics.RigidBodyAPI(prim)
                    rec["kinematic"] = bool(rb.GetKinematicEnabledAttr().Get())
                else:
                    rec["kinematic"] = None
            except Exception:
                rec["kinematic"] = None
            try:
                if prim.HasAPI(UsdPhysics.MassAPI):
                    rec["mass"] = round(
                        float(UsdPhysics.MassAPI(prim).GetMassAttr().Get()), 4)
                else:
                    rec["mass"] = None
            except Exception:
                rec["mass"] = None
            try:
                if UsdPhysics.Scene(prim):
                    out["physics_scene"] = path
            except Exception:
                pass
            out["prims"].append(rec)
            tname = prim.GetTypeName()
            if "Joint" in tname and tname.startswith("Physics"):
                try:
                    j = UsdPhysics.Joint(prim)
                    out["joints"].append({
                        "path": path,
                        "type": tname,
                        "body0": [str(t) for t in
                                  j.GetBody0Rel().GetTargets()],
                        "body1": [str(t) for t in
                                  j.GetBody1Rel().GetTargets()],
                    })
                except Exception:
                    pass
        except Exception:
            continue
    rigid_paths = [r["path"] for r in out["prims"] if r.get("rigid") is True]
    playing = out["timeline"].get("playing") is True
    rested = (not playing) and (out["timeline"].get("t") or 0) > 0
    if (playing or rested) and rigid_paths:
        try:
            from isaacsim.core.experimental.prims import RigidPrim
            rp = RigidPrim(paths=rigid_paths)
            pos = rp.get_world_poses()[0].numpy()
            by_path = {r["path"]: r for r in out["prims"]}
            for i, p in enumerate(rigid_paths):
                by_path[p]["sim"] = [round(float(pos[i][0]), 4),
                                     round(float(pos[i][1]), 4),
                                     round(float(pos[i][2]), 4)]
        except Exception:
            pass
    return out


def describe() -> str:
    try:
        import omni.usd  # noqa: F401
        return "watcher: ready (USD stage diff)"
    except Exception:
        return "watcher: unavailable (not running inside Isaac Sim)"
