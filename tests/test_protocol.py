"""Offline tests: stdlib only, no Isaac Sim needed. Run: python tests/test_protocol.py"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"arexec_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


protocol = _load("protocol")
handlers = _load("handlers")  # must import with guarded Isaac deps
catalog = protocol.load_catalog(ROOT / "actions_compact.json")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def expect_validation_error(fn, needle):
    try:
        fn()
    except protocol.ValidationError as exc:
        assert needle in str(exc), f"missing {needle!r} in {exc}"
        return
    raise AssertionError(f"expected ValidationError with {needle!r}")


def test_parse_batch():
    batch = protocol.parse_batch("# hello\n\ncreate.objects.cuboid size=1 pos=0,0,0.5  # drop\nsim.play\n")
    assert [(k, n) for k, _, n in batch] == [("create.objects.cuboid", 3), ("sim.play", 4)], batch
    assert batch[0][1] == {"size": "1", "pos": "0,0,0.5"}, batch[0][1]


def test_parse_bad_token():
    try:
        protocol.parse_batch("sim.play now")
    except protocol.ProtocolError as exc:
        assert "key=value" in str(exc)
        return
    raise AssertionError("expected ProtocolError")


def test_validate_defaults():
    a = protocol.validate("create.objects.cuboid", {}, catalog, lineno=1)
    assert a.params["size"] == 1.0 and a.params["pos"] == [0.0, 0.0, 0.5], a.params
    assert a.params["mass"] == 1.0


def test_cuboid_clamp_warns():
    a = protocol.validate("create.objects.cuboid", {"size": "2", "pos": "0,0,0.1"}, catalog, lineno=7)
    assert a.params["pos"][2] == 1.0, a.params
    assert len(a.warnings) == 1 and "line 7" in a.warnings[0], a.warnings


def test_sphere_clamp():
    a = protocol.validate("create.objects.sphere", {"radius": "0.5", "pos": "0,0,0.0"}, catalog)
    assert a.params["pos"][2] == 0.5, a.params


def test_mass_must_be_positive():
    expect_validation_error(
        lambda: protocol.validate("physics.set.mass", {"target": "x", "value": "0"}, catalog, lineno=2),
        "value' must be > 0",
    )


def test_step_n():
    expect_validation_error(
        lambda: protocol.validate("sim.step", {"n": "0"}, catalog), "n' must be >= 1"
    )


def test_unknown_action_suggests():
    expect_validation_error(
        lambda: protocol.validate("create.objects.cube", {}, catalog), "did you mean"
    )


def test_unavailable_rejected():
    dead = next(k for k, v in catalog.items() if not v.get("available"))
    expect_validation_error(lambda: protocol.validate(dead, {}, catalog), "unavailable")


def test_unknown_param():
    expect_validation_error(
        lambda: protocol.validate("sim.play", {"speed": "2"}, catalog), "unknown param 'speed'"
    )


def test_bad_types():
    expect_validation_error(
        lambda: protocol.validate("create.objects.cuboid", {"size": "abc"}, catalog), "wants float"
    )
    expect_validation_error(
        lambda: protocol.validate("create.objects.cuboid", {"pos": "0,0"}, catalog), "3 comma values"
    )


def test_name_allowed_only_on_create():
    a = protocol.validate("create.objects.cuboid", {"name": "boxy"}, catalog)
    assert a.params["name"] == "boxy"
    expect_validation_error(
        lambda: protocol.validate("sim.play", {"name": "x"}, catalog), "unknown param 'name'"
    )


def test_joint_valid_with_extras():
    a = protocol.validate(
        "joint.create.joint",
        {"joint_type": "Revolute", "from_prim": "chassis", "to_prim": "wheel"},
        catalog,
    )
    assert a.params["joint_type"] == "revolute", a.params
    assert a.params["axis"] == "Z", a.params
    assert a.params["stage"] is None, a.params  # auto-injected, not prompted


def test_joint_bad_type_and_axis():
    expect_validation_error(
        lambda: protocol.validate(
            "joint.create.joint",
            {"joint_type": "hinge", "from_prim": "a", "to_prim": "b"},
            catalog,
        ),
        "joint_type must be one of",
    )
    expect_validation_error(
        lambda: protocol.validate(
            "joint.create.joint",
            {"joint_type": "fixed", "from_prim": "a", "to_prim": "b", "axis": "W"},
            catalog,
        ),
        "axis must be",
    )
    a = protocol.validate(
        "joint.create.joint",
        {"joint_type": "fixed", "from_prim": "a", "to_prim": "b", "axis": "y", "name": "j1"},
        catalog,
    )
    assert a.params["axis"] == "Y" and a.params["name"] == "j1", a.params


def test_string_vec3_default_coerced():
    a = protocol.validate("sensor.do.range_sensor_create_generic", {}, catalog)
    assert a.params["translation"] == [0.0, 0.0, 0.0], a.params["translation"]
    assert a.params["path"] == "/GenericSensor", a.params["path"]


def test_material_add_requires_path_not_stage():
    expect_validation_error(
        lambda: protocol.validate("material.add.rigid_body_material", {}, catalog),
        "missing required param 'path'",
    )
    a = protocol.validate(
        "material.add.rigid_body_material",
        {"path": "/World/Looks/rubber", "staticFriction": "0.9"},
        catalog,
    )
    assert a.params["stage"] is None
    assert a.params["staticFriction"] == "0.9", a.params  # handler converts


def test_lidar_extras():
    a = protocol.validate(
        "sensor.create.rtx_lidar", {"path": "lidar_top", "tick_rate": "20"}, catalog
    )
    assert a.params["path"] == "lidar_top" and a.params["tick_rate"] == 20.0, a.params


def test_lidar_config_and_pos_extras():
    a = protocol.validate(
        "sensor.create.rtx_lidar",
        {"path": "think_cube/ride", "config": "Example_Rotary_2D",
         "pos": "2.7,0.0,0.9"},
        catalog,
    )
    assert a.params["config"] == "Example_Rotary_2D", a.params
    assert tuple(a.params["pos"]) == (2.7, 0.0, 0.9), a.params


def test_articulation_and_drive_signatures():
    a = protocol.validate("robot.add.articulation", {"path": "chassis"}, catalog)
    assert a.params["path"] == "chassis"
    b = protocol.validate("robot.set.joint_drive", {"target": "j1"}, catalog)
    assert (b.params["stiffness"], b.params["damping"], b.params["max_force"]) == (
        10000.0, 1000.0, 10000.0), b.params


def test_joint_drive_velocity_extras():
    b = protocol.validate(
        "robot.set.joint_drive", {"target": "j1", "target_velocity": "5"}, catalog
    )
    assert b.params["target_velocity"] == 5.0, b.params
    assert b.params["target_position"] is None, b.params


def test_handlers_cover_available_catalog_subset():
    for key in handlers.HANDLED_ACTIONS:
        assert key in catalog, f"handler {key} missing from catalog"
        assert catalog[key].get("available"), f"handler {key} unavailable"
        meth = "_do_" + key.replace(".", "_")
        assert hasattr(handlers.Executor, meth), f"Executor.{meth} missing"


def test_new_shape_defaults_and_clamps():
    a = protocol.validate("create.objects.cylinder", {}, catalog)
    assert (a.params["radius"], a.params["height"], a.params["mass"]) == (0.4, 1.0, 1.0)
    b = protocol.validate("create.objects.cylinder", {"pos": "0,0,0"}, catalog, lineno=3)
    assert b.params["pos"][2] == 0.5, b.params
    assert len(b.warnings) == 1 and "line 3" in b.warnings[0], b.warnings
    c = protocol.validate("create.objects.fixed_cuboid", {}, catalog)
    assert "mass" not in c.params and c.params["size"] == 1.0
    d = protocol.validate("create.objects.capsule", {"pos": "0,0,0.1"}, catalog)
    assert d.params["pos"][2] == 0.5, d.params  # max(height/2, radius)


def test_sim_tuning_signatures():
    a = protocol.validate("sim.set.gravity", {}, catalog)
    assert a.params["value"] == [0, 0, -9.81], a.params
    b = protocol.validate("sim.set.dt", {"physics": "0.01"}, catalog)
    assert b.params["physics"] == 0.01 and b.params["rendering"] > 0.016


def test_import_signatures():
    a = protocol.validate("import.robot.urdf", {"path": "r/urdf/bot.urdf"}, catalog)
    assert a.params["path"] == "r/urdf/bot.urdf"
    assert a.params["fix_base"] is False and a.params["merge_fixed_joints"] is True
    b = protocol.validate("import.asset.usd", {"path": "x/y.usd"}, catalog)
    assert b.params["pos"] is None and b.params["name"] is None


def test_robot_limit_rules():
    expect_validation_error(
        lambda: protocol.validate("robot.set.velocity_limit", {"target": "j", "value": "0"}, catalog),
        "value' must be > 0",
    )
    expect_validation_error(
        lambda: protocol.validate("robot.clone", {"target": "x", "count": "0"}, catalog),
        "count' must be >= 1",
    )
    expect_validation_error(
        lambda: protocol.validate("robot.clone", {"target": "x", "count": "21"}, catalog),
        "capped at 20",
    )
    a = protocol.validate("robot.clone", {"target": "x"}, catalog)
    assert a.params["count"] == 2


def test_physics_scene_requires_path():
    expect_validation_error(
        lambda: protocol.validate("physics.add.physics_scene", {}, catalog),
        "missing required param 'path'",
    )
    a = protocol.validate("physics.set.rigid_body", {"path": "x"}, catalog)
    assert a.params["approximationShape"] == "convexHull", a.params
    assert a.params["kinematic"] is False


def test_radar_extras_and_quat_passthrough():
    a = protocol.validate("sensor.create.rtx_radar", {"tick_rate": "15"}, catalog)
    assert a.params["tick_rate"] == 15.0, a.params
    assert a.params["translation"] == [0.0, 0.0, 0.0], a.params
    assert a.params["orientation"] == "(1, 0, 0, 0)", a.params
    b = protocol.validate("sensor.create.rtx_ultrasonic", {}, catalog)
    assert b.params["tick_rate"] is None


def test_create_orient_scale_accepted():
    keys = [k for k in handlers.HANDLED_ACTIONS
            if k.startswith("create.") and k != "create.objects.plane"]
    assert len(keys) == 15, keys
    for key in keys:
        a = protocol.validate(key, {"orient": "0.7071,0,0,0.7071", "scale": "1,2,1"},
                              catalog, lineno=1)
        assert a.params["orient"] == [0.7071, 0.0, 0.0, 0.7071], (key, a.params)
        assert a.params["scale"] == [1.0, 2.0, 1.0], (key, a.params)
    a = protocol.validate("create.objects.cuboid", {}, catalog)
    assert a.params["orient"] is None and a.params["scale"] is None


def test_create_orient_bad_length():
    expect_validation_error(
        lambda: protocol.validate("create.objects.cuboid", {"orient": "0,0,1"}, catalog),
        "wants 4 comma values",
    )
    expect_validation_error(
        lambda: protocol.validate("create.objects.sphere", {"scale": "1,1"}, catalog),
        "wants 3 comma values",
    )


def test_plane_rejects_orient_scale():
    expect_validation_error(
        lambda: protocol.validate("create.objects.plane", {"orient": "0,0,0,1"}, catalog),
        "unknown param 'orient'",
    )
    expect_validation_error(
        lambda: protocol.validate("create.objects.plane", {"scale": "2,2,2"}, catalog),
        "unknown param 'scale'",
    )


def test_scaled_spawn_clamp():
    a = protocol.validate("create.objects.cuboid",
                          {"size": "1", "scale": "1,1,2", "pos": "0,0,0.2"}, catalog)
    assert a.params["pos"] == [0.0, 0.0, 1.0], a.params
    assert any("size/2" in w for w in a.warnings), a.warnings
    b = protocol.validate("create.objects.sphere",
                          {"radius": "0.5", "pos": "0,0,0.1"}, catalog)
    assert b.params["pos"] == [0.0, 0.0, 0.5], b.params  # unscaled path unchanged


def test_set_pose_orient_vec4():
    a = protocol.validate("physics.set.pose", {"target": "x", "orient": "0,0,0,1"}, catalog)
    assert a.params["orient"] == [0.0, 0.0, 0.0, 1.0], a.params
    assert a.params["pos"] is None


def test_create_help_shows_transform():
    sig = protocol.help_line("create.objects.cylinder", catalog["create.objects.cylinder"])
    assert "[orient]" in sig and "[scale]" in sig, sig


def test_backslash_path_normalized():
    key, raw = protocol.parse_line(
        "scene.open path=C:\\isaacsim\\stages\\dwa_final.usd", lineno=1)
    assert key == "scene.open", (key, raw)
    assert raw == {"path": "C:/isaacsim/stages/dwa_final.usd"}, raw
    a = protocol.validate("scene.open", raw, catalog, lineno=1)
    assert a.params["path"] == "C:/isaacsim/stages/dwa_final.usd", a.params


def test_backslash_prim_target_normalized():
    key, raw = protocol.parse_line(
        "scene.delete.prim target=\\World\\oops", lineno=1)
    assert raw == {"target": "/World/oops"}, raw
    a = protocol.validate("scene.delete.prim", raw, catalog, lineno=1)
    assert a.params["target"] == "/World/oops", a.params


def test_delete_physics_scene_refused():
    for target in ("PhysicsScene", "/World/PhysicsScene", "/PhysicsScene",
                   "/World/PhysicsScene/"):
        expect_validation_error(
            lambda t=target: protocol.validate(
                "scene.delete.prim", {"target": t}, catalog, lineno=2),
            "refusing to delete the PhysicsScene",
        )


def test_delete_ordinary_prim_allowed():
    a = protocol.validate("scene.delete.prim", {"target": "/World/oops"},
                          catalog, lineno=1)
    assert a.params["target"] == "/World/oops", a.params
    b = protocol.validate("scene.delete.prim", {"target": "wheel_cyl_fl"},
                          catalog, lineno=1)
    assert b.params["target"] == "wheel_cyl_fl", b.params


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
