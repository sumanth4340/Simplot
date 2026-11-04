"""Tests for the reflex dispatcher. Run: python tests/test_reflex.py"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arrx_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


protocol = _load("protocol", EXT_PY / "protocol.py")
handlers = _load("handlers", EXT_PY / "handlers.py")
reasoner = _load("reasoner", EXT_PY / "reasoner.py")
reflex = _load("reflex", EXT_PY / "reflex.py")
catalog = protocol.load_catalog(ROOT / "actions_compact.json")
HANDLED = set(handlers.HANDLED_ACTIONS)

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _validated_lines(text):
    batch = protocol.parse_batch(text)
    assert batch, "reflex emitted no runnable lines"
    for key, raw, lineno in batch:
        action = protocol.validate(key, raw, catalog, lineno=lineno)
        assert action.key in HANDLED, f"reflex emitted unhandled {key}"
        assert catalog[action.key].get("available"), f"dead in reflex: {key}"
    return [k for k, _, _ in batch]


def test_create_cube_hits_with_exact_lines():
    hit = reflex.try_reflex("create a cube")
    assert hit is not None, "flagship command fell through to the LLM"
    text, notes = hit
    assert text.splitlines() == [
        "create.objects.plane size=20",
        "create.objects.cuboid pos=0.5,0,2",
    ], text
    assert notes and notes[0].startswith("reflex planner (no LLM call)")
    _validated_lines(text)


def test_two_red_spheres_count_color_layout():
    hit = reflex.try_reflex("make two red spheres")
    assert hit is not None
    text, _ = hit
    keys = _validated_lines(text)
    assert keys == ["create.objects.plane",
                    "create.objects.sphere",
                    "create.objects.sphere"], keys
    lines = text.splitlines()[1:]
    assert all("color=1,0,0" in line for line in lines), text
    positions = [line.split("pos=")[1].split()[0] for line in lines]
    assert len(set(positions)) == 2, f"overlapping spawn: {text}"


def test_size_adjective_scales_dims():
    hit = reflex.try_reflex("create a big cube")
    assert hit is not None
    text, _ = hit
    assert "size=2" in text, text
    _validated_lines(text)


def test_play_suffix_allowed_on_shape():
    hit = reflex.try_reflex("create a cube and play")
    assert hit is not None
    keys = _validated_lines(hit[0])
    assert keys[-1] == "sim.play", keys


def test_compositional_tasks_fall_through():
    for task in ("make two spheres attached to the cube",
                 "attach a sphere to the cube",
                 "drive the rover forward",
                 "make a heavy cube",
                 "add a lidar",
                 "red cube and blue sphere",
                 "stack three cubes"):
        assert reflex.try_reflex(task) is None, f"reflex grabbed: {task!r}"


def test_transport_commands():
    assert reflex.try_reflex("play")[0].splitlines() == ["sim.play"]
    assert reflex.try_reflex("pause the sim")[0].splitlines() == ["sim.pause"]
    assert reflex.try_reflex("stop")[0].splitlines() == ["sim.stop"]
    assert reflex.try_reflex("play then pause") is None


def test_delete_needs_name_like_target():
    hit = reflex.try_reflex("delete cube_01")
    assert hit is not None
    assert hit[0].splitlines() == ["scene.delete.prim target=cube_01"]
    _validated_lines(hit[0])
    for task in ("delete the cube", "delete it", "delete everything",
                 "remove the red sphere"):
        assert reflex.try_reflex(task) is None, f"reflex grabbed: {task!r}"


def test_plane_skipped_when_snapshot_has_one():
    hit = reflex.try_reflex("create a cube", "sim: paused\nstage: GroundPlane")
    assert hit is not None
    keys = _validated_lines(hit[0])
    assert keys == ["create.objects.cuboid"], keys


def test_gibberish_falls_through():
    for task in ("do a backflip", "how do joints work?", "", "   ",
                 "cube", "please"):
        assert reflex.try_reflex(task) is None, f"reflex grabbed: {task!r}"


def test_count_capped_at_six():
    hit = reflex.try_reflex("create 20 cubes")
    assert hit is not None
    text, notes = hit
    keys = _validated_lines(text)
    assert keys.count("create.objects.cuboid") == 6, keys
    assert any("capped" in note for note in notes), notes


def test_reflex_is_single_pass_in_loops():
    assert reasoner.check_backend(step_no=1, backend="reflex") is None
    reason = reasoner.check_backend(step_no=2, backend="reflex")
    assert reason and "reflex" in reason, reason
    session = reasoner.ReasonerSession(task="create a cube")
    session.record(reasoner.StepRecord(step=1, actions_text="a",
                                      backend="reflex", results=[], ok=True))
    decision, _ = reasoner.decide_after_run(session, "reflex")
    assert decision == "done", decision
    session.steps[-1].ok = False
    decision, _ = reasoner.decide_after_run(session, "reflex")
    assert decision == "failed", decision


class _FakeRel:
    def __init__(self, targets):
        self._targets = targets

    def GetTargets(self):
        return list(self._targets)


class _FakePrim:
    def __init__(self, path, rels=None, apis=(), parent=None):
        self._path = path
        self._rels = rels or {}
        self._apis = set(apis)
        self._parent = parent

    def GetRelationship(self, name):
        if name not in self._rels:
            raise ValueError(f"no relationship {name}")
        return _FakeRel(self._rels[name])

    def GetPath(self):
        return self._path

    def IsValid(self):
        return True

    def HasAPI(self, api):
        return api in self._apis

    def GetParent(self):
        return self._parent


class _FakeStage:
    def __init__(self, prims):
        self._prims = prims

    def GetPrimAtPath(self, path):
        return self._prims[str(path)]


class _FakeUsdPhysics:
    ArticulationRootAPI = "ArticulationRootAPI"


def _with_fake_stage(prims):
    real_stage = handlers._stage
    real_physics = getattr(handlers, "UsdPhysics", None)
    stage = _FakeStage(prims)
    handlers._stage = lambda: stage
    handlers.UsdPhysics = _FakeUsdPhysics
    return real_stage, real_physics


def _restore_fakes(real_stage, real_physics):
    handlers._stage = real_stage
    if real_physics is None:
        del handlers.UsdPhysics
    else:
        handlers.UsdPhysics = real_physics


def test_velocity_limit_clamps_joint_drives():
    root = _FakePrim("/World/car", apis=("ArticulationRootAPI",))
    joint = _FakePrim("/World/Joints/j", {"physics:body0": ["/World/car"]})
    real = _with_fake_stage({"/World/car": root,
                             "/World/Joints/j": joint})
    try:
        inst = handlers.Executor()
        inst._vel_limits["/World/car"] = 1.0  # rad/s -> 57.3 deg/s cap
        assert abs(inst._clamp_to_velocity_limit(joint, 114.6) - 57.296) < 0.01
        assert abs(inst._clamp_to_velocity_limit(joint, -114.6) + 57.296) < 0.01
        assert inst._clamp_to_velocity_limit(joint, 30.0) == 30.0
    finally:
        _restore_fakes(*real)


def test_velocity_limit_passthrough_unresolvable():
    joint = _FakePrim("/World/Joints/j", {})
    real = _with_fake_stage({"/World/Joints/j": joint})
    try:
        inst = handlers.Executor()
        assert inst._clamp_to_velocity_limit(joint, 200.0) == 200.0
    finally:
        _restore_fakes(*real)


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
