"""Offline tests for the sense watchdog. Run: python tests/test_watcher.py"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"arwch_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


watcher = _load("watcher")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _prim(path, pos=None, rigid=False, collision=False, mass=None, sim=None):
    rec = {"path": path, "type": "Cube", "pos": pos or [0.0, 0.0, 0.0],
           "rigid": rigid, "collision": collision, "kinematic": None,
           "mass": mass}
    if sim is not None:
        rec["sim"] = sim
    return rec


def _snap(prims, playing=False, joints=None, scene="/World/PhysicsScene"):
    return {"prims": prims, "joints": joints or [],
            "timeline": {"playing": playing, "t": 1.5},
            "physics_scene": scene}


BASE = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 0.5], rigid=True,
                    collision=True, mass=1.0, sim=[1.0, 2.0, 0.5]),
              _prim("/World/Ground")],
             joints=[{"path": "/World/Joint_01", "type": "PhysicsRevoluteJoint",
                      "body0": ["/World/Cube_01"], "body1": []}])


def test_imports_outside_isaac_and_capture_none():
    assert watcher.capture_compact() is None
    assert "unavailable" in watcher.describe()


def test_quiet_on_identical():
    assert watcher.diff_snapshots(BASE, BASE) == []


def test_quiet_on_sub_mm_jitter():
    moved = _snap([_prim("/World/Cube_01", pos=[1.0004, 2.0, 0.5],
                          rigid=True, collision=True, mass=1.0,
                          sim=[1.0, 2.0, 0.5]),
                   _prim("/World/Ground")],
                  joints=BASE["joints"])
    assert watcher.diff_snapshots(BASE, moved) == []


def test_prim_added_removed():
    after = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 0.5],
                          rigid=True, collision=True, mass=1.0,
                          sim=[1.0, 2.0, 0.5]),
                   _prim("/World/Ground"),
                   _prim("/World/Cube_02", pos=[3.0, 0.0, 0.5])],
                  joints=BASE["joints"])
    ev = watcher.diff_snapshots(BASE, after)
    assert ev == ["event.stage.prim_added path=/World/Cube_02 type=Cube"], ev
    ev = watcher.diff_snapshots(after, BASE)
    assert ev == ["event.stage.prim_removed path=/World/Cube_02"], ev


def test_pose_moved_authored():
    before = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 0.5])])
    after = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 1.2])])
    ev = watcher.diff_snapshots(before, after)
    assert len(ev) == 1 and ev[0].startswith("event.pose.moved path=/World/Cube_01"), ev
    assert "dz=0.700" in ev[0] and "src=sim" not in ev[0], ev


def test_pose_moved_prefers_sim():
    after = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 0.5],
                          rigid=True, collision=True, mass=1.0,
                          sim=[1.0, 2.0, 0.3]),
                   _prim("/World/Ground")],
                  joints=BASE["joints"])
    ev = watcher.diff_snapshots(BASE, after)
    assert len(ev) == 1 and "src=sim" in ev[0] and "dz=-0.200" in ev[0], ev


def test_physics_flag_and_mass():
    after = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 0.5],
                          rigid=True, collision=True, mass=2.0,
                          sim=[1.0, 2.0, 0.5]),
                   _prim("/World/Ground", rigid=True)],
                  joints=BASE["joints"])
    ev = watcher.diff_snapshots(BASE, after)
    assert "event.physics.changed path=/World/Ground rigid=False->True" in ev, ev
    assert "event.mass.changed path=/World/Cube_01 1.0000->2.0000" in ev, ev


def test_joint_added_removed():
    after = _snap(BASE["prims"], joints=[])
    ev = watcher.diff_snapshots(BASE, after)
    assert ev == ["event.joint.removed path=/World/Joint_01"], ev
    ev = watcher.diff_snapshots(after, BASE)
    assert ev == ["event.joint.added path=/World/Joint_01 type=PhysicsRevoluteJoint"], ev


def test_timeline_transitions_and_none_safe():
    assert watcher.diff_snapshots(_snap([], playing=False),
                                  _snap([], playing=True)) == ["event.timeline.started"]
    assert watcher.diff_snapshots(_snap([], playing=True),
                                  _snap([], playing=False)) == ["event.timeline.stopped"]
    assert watcher.diff_snapshots({"prims": []}, {"prims": []}) == []


def test_motion_skipped_when_asked():
    before = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 0.5])], playing=True)
    after = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 1.2])], playing=True)
    assert watcher.diff_snapshots(before, after, include_motion=False) == []
    assert len(watcher.diff_snapshots(before, after)) == 1


def test_overflow_collapses_to_resync():
    many = [_prim(f"/World/P_{i:03d}") for i in range(60)]
    ev = watcher.diff_snapshots(_snap([]), _snap(many))
    assert len(ev) == 1 and ev[0].startswith("event.stage.resync "), ev
    assert "after_prims=60" in ev[0], ev


def test_hash_order_independent_and_change_sensitive():
    a = _snap([_prim("/World/B"), _prim("/World/A")])
    b = _snap([_prim("/World/A"), _prim("/World/B")])
    assert watcher.snapshot_hash(a) == watcher.snapshot_hash(b)
    c = _snap([_prim("/World/A"), _prim("/World/B", pos=[0.0, 0.0, 1.0])])
    assert watcher.snapshot_hash(a) != watcher.snapshot_hash(c)
    # clock t is not part of the hash: same state, different t -> quiet
    d = {"prims": a["prims"], "joints": [], "timeline": {"playing": False, "t": 99.0},
         "physics_scene": a["physics_scene"]}
    assert watcher.snapshot_hash(a) == watcher.snapshot_hash(d)


def test_watcher_fires_once_then_quiet():
    w = watcher.Watcher()
    assert w.observe(BASE) == []  # first observation establishes baseline
    after = _snap([_prim("/World/Cube_01", pos=[1.0, 2.0, 0.5],
                          rigid=True, collision=True, mass=1.0,
                          sim=[1.0, 2.0, 0.5]),
                   _prim("/World/Ground"),
                   _prim("/World/Cube_02", pos=[3.0, 0.0, 0.5])],
                  joints=BASE["joints"])
    ev = w.observe(after)
    assert ev == ["event.stage.prim_added path=/World/Cube_02 type=Cube"], ev
    assert w.observe(after) == []  # adopted: quiet now
    assert w.baseline_hash == watcher.snapshot_hash(after)


def test_watcher_quiet_while_playing_motion():
    w = watcher.Watcher()
    p0 = _snap([_prim("/World/Ball", pos=[0.0, 0.0, 5.0], rigid=True,
                       sim=[0.0, 0.0, 5.0])], playing=True)
    p1 = _snap([_prim("/World/Ball", pos=[0.0, 0.0, 5.0], rigid=True,
                       sim=[0.0, 0.0, 4.0])], playing=True)
    assert w.observe(p0) == []
    assert w.observe(p1) == []  # motion while playing: no spam
    p2 = _snap([_prim("/World/Ball", pos=[0.0, 0.0, 5.0], rigid=True,
                       sim=[0.0, 0.0, 0.5])], playing=False)
    ev = w.observe(p2)
    assert "event.timeline.stopped" in ev, ev
    assert any(e.startswith("event.pose.moved") for e in ev), ev


def test_observe_none_safe_and_establish_silent():
    w = watcher.Watcher()
    assert w.observe(None) == []
    w.establish(BASE)
    assert w.observe(BASE) == []
    assert w.observe_after(None, BASE) == []
    assert w.baseline_hash == watcher.snapshot_hash(BASE)


if __name__ == "__main__":
    for name, fn in sorted({k: v for k, v in globals().items()
                            if k.startswith("test_")}.items()):
        check(name, fn)
    print(f"\n{len(passed)}/{len(passed)} watcher tests passed")
