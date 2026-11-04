"""Live action handlers: validated actions -> Isaac Sim stage.

All Isaac/Kit imports are guarded so this module still imports outside
Isaac Sim (the GUI and tests can read HANDLED_ACTIONS anywhere).
"""
from __future__ import annotations

import asyncio
import math
import os

try:
    import carb
    import omni.timeline
    import omni.usd
    from pxr import Gf, Sdf, Tf, UsdGeom, UsdPhysics, UsdShade

    _USD_OK = True
except Exception:  # pragma: no cover - outside Kit
    _USD_OK = False

try:
    from pxr import PhysxSchema

    _PHYSX_SCHEMA_OK = True
except Exception:
    try:
        import PhysxSchema  # third-party schemas import top-level

        _PHYSX_SCHEMA_OK = True
    except Exception:  # pragma: no cover - outside Kit
        _PHYSX_SCHEMA_OK = False

try:
    from isaacsim.sensors.experimental.rtx import Lidar

    _LIDAR_OK = True
except Exception:  # pragma: no cover - extension missing
    _LIDAR_OK = False

try:
    import numpy as np
    from isaacsim.core.api.objects import DynamicCuboid, DynamicSphere, GroundPlane
    from isaacsim.core.api.world import World

    _CORE_OK = True
except Exception:  # pragma: no cover - outside Isaac Sim
    _CORE_OK = False

try:
    from isaacsim.core.experimental.prims import RigidPrim

    _PRIMS_OK = True
except Exception:  # pragma: no cover - outside Isaac Sim
    _PRIMS_OK = False

HANDLED_ACTIONS = (
    "create.objects.plane",
    "create.objects.cuboid",
    "create.objects.sphere",
    "create.objects.cylinder",
    "create.objects.cone",
    "create.objects.capsule",
    "create.objects.fixed_cuboid",
    "create.objects.fixed_sphere",
    "create.objects.fixed_cylinder",
    "create.objects.fixed_cone",
    "create.objects.fixed_capsule",
    "create.objects.visual_cuboid",
    "create.objects.visual_sphere",
    "create.objects.visual_cylinder",
    "create.objects.visual_cone",
    "create.objects.visual_capsule",
    "physics.add.rigid_body",
    "physics.remove.rigid_body",
    "physics.add.collider",
    "physics.remove.collider",
    "physics.add.physics_scene",
    "physics.set.mass",
    "physics.set.pose",
    "physics.set.velocity",
    "physics.set.rigid_body",
    "physics.set.static_collider",
    "joint.create.joint",
    "robot.add.articulation",
    "robot.set.joint_drive",
    "robot.set.torque",
    "robot.set.torque_limit",
    "robot.set.velocity_limit",
    "robot.clone",
    "material.add.rigid_body_material",
    "material.bind.material",
    "sensor.create.rtx_lidar",
    "sensor.create.rtx_radar",
    "sensor.create.rtx_ultrasonic",
    "sensor.do.range_sensor_create_generic",
    "sensor.do.range_sensor_create_lidar",
    "sensor.create.light_beam_sensor",
    "import.robot.urdf",
    "import.robot.mjcf",
    "import.asset.usd",
    "import.asset.heightmap",
    "export.asset.urdf",
    "scene.create.prim",
    "scene.delete.prim",
    "scene.save",
    "scene.open",
    "sim.play",
    "sim.pause",
    "sim.stop",
    "sim.step",
    "sim.reset",
    "sim.set.gravity",
    "sim.set.dt",
)

_NAME_PREFIX = {
    "create.objects.plane": "ground_plane",
    "create.objects.cuboid": "cube",
    "create.objects.sphere": "sphere",
    "create.objects.cylinder": "cylinder",
    "create.objects.cone": "cone",
    "create.objects.capsule": "capsule",
    "create.objects.fixed_cuboid": "fixed_cube",
    "create.objects.fixed_sphere": "fixed_sphere",
    "create.objects.fixed_cylinder": "fixed_cylinder",
    "create.objects.fixed_cone": "fixed_cone",
    "create.objects.fixed_capsule": "fixed_capsule",
    "create.objects.visual_cuboid": "vis_cube",
    "create.objects.visual_sphere": "vis_sphere",
    "create.objects.visual_cylinder": "vis_cylinder",
    "create.objects.visual_cone": "vis_cone",
    "create.objects.visual_capsule": "vis_capsule",
    "sensor.create.rtx_lidar": "lidar",
    "sensor.create.rtx_radar": "radar",
    "sensor.create.rtx_ultrasonic": "ultrasonic",
    "sensor.do.range_sensor_create_generic": "range",
    "sensor.do.range_sensor_create_lidar": "scan",
    "sensor.create.light_beam_sensor": "beam",
    "import.robot.urdf": "robot",
    "import.robot.mjcf": "robot",
    "import.asset.usd": "asset",
}

def _joint_class(joint_type: str):
    return {
        "fixed": UsdPhysics.FixedJoint,
        "revolute": UsdPhysics.RevoluteJoint,
        "prismatic": UsdPhysics.PrismaticJoint,
        "spherical": UsdPhysics.SphericalJoint,
        "distance": UsdPhysics.DistanceJoint,
    }[joint_type]


def _timeline():
    return omni.timeline.get_timeline_interface()


def _stage():
    return omni.usd.get_context().get_stage()


def _timeline_info() -> str:
    """Current/end timeline time for the snapshot. Never raises."""
    try:
        tl = _timeline()
        return f" t={tl.get_current_time():.2f}/{tl.get_end_time():.2f}"
    except Exception:
        return ""


class Executor:
    """Owns the name->prim registry and runs validated actions."""

    def __init__(self):
        self.objects = {}  # name -> prim path
        self._counters = {}
        self._world = None
        self._world_failed = False

    # -- helpers ---------------------------------------------------------
    def _unique_name(self, key: str) -> str:
        prefix = _NAME_PREFIX.get(key, "obj")
        if key == "create.objects.plane":
            return prefix
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}_{self._counters[prefix]:02d}"

    def _ensure_world_root(self, stage):
        if not stage.GetPrimAtPath("/World").IsValid():
            stage.DefinePrim("/World", "Xform")

    def resolve_target(self, target: str):
        """Resolve a registry name or prim path -> prim path, or None."""
        if target in self.objects:
            return self.objects[target]
        path = target if target.startswith("/") else f"/World/{target}"
        try:
            prim = _stage().GetPrimAtPath(path)
        except Exception:
            return None
        return path if prim.IsValid() else None

    def _get_world(self):
        if not _CORE_OK or self._world_failed:
            return None
        if self._world is not None:
            return self._world
        try:
            self._world = World()
        except Exception:
            self._world_failed = True
            return None
        return self._world

    def is_playing(self) -> bool:
        try:
            return bool(_timeline().is_playing())
        except Exception:
            return False

    def _need_paused(self):
        if self.is_playing():
            return False, "pause the sim first (timeline is playing)"
        return True, ""

    @staticmethod
    def _apply_orient_scale(prim, p: dict) -> None:
        """Apply validated orient ([x,y,z,w]) and scale ([x,y,z]) to a prim.

        Shared by every shape creator so all 3D models inherit the full
        transform. Reuses existing ops when the creator authored them.
        """
        orient = p.get("orient")
        scale = p.get("scale")
        if orient is None and scale is None:
            return
        xform = UsdGeom.Xformable(prim)
        if orient is not None:
            x, y, z, w = orient
            op = next(
                (o for o in xform.GetOrderedXformOps()
                 if o.GetOpType() == UsdGeom.XformOp.TypeOrient),
                None,
            )
            if op is None:
                op = xform.AddOrientOp()
            op.Set(Gf.Quatf(w, x, y, z))
        if scale is not None:
            op = next(
                (o for o in xform.GetOrderedXformOps()
                 if o.GetOpType() == UsdGeom.XformOp.TypeScale),
                None,
            )
            if op is None:
                op = xform.AddScaleOp()
            op.Set(Gf.Vec3f(*scale))

    @staticmethod
    def _world_orient(prim):
        """World-space orientation, walking up the chain (identity default)."""
        acc = Gf.Quatf(1, 0, 0, 0)
        chain = []
        node = prim
        while node.IsValid():
            chain.append(node)
            node = node.GetParent()
        for node in reversed(chain):
            for op in UsdGeom.Xformable(node).GetOrderedXformOps():
                if op.GetOpType() == UsdGeom.XformOp.TypeOrient:
                    v = op.Get()
                    if v is not None:
                        imag = v.GetImaginary()
                        acc = acc * Gf.Quatf(v.GetReal(), imag[0], imag[1], imag[2])
                    break
        return acc

    @staticmethod
    def _world_translate(prim):
        """World-space translation, walking up the chain.

        Assumes no rotations/scales on the chain (true for executor-built
        robots until set.pose gains orient use); joint frames document this.
        """
        pos = Gf.Vec3d(0, 0, 0)
        node = prim
        while node.IsValid():
            for op in UsdGeom.Xformable(node).GetOrderedXformOps():
                if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                    value = op.Get()
                    if value is not None:
                        pos += Gf.Vec3d(value)
                    break
            node = node.GetParent()
        return pos

    # -- entrypoint ------------------------------------------------------
    def run(self, action) -> tuple:
        """Run a ValidatedAction -> (ok, message)."""
        if not _USD_OK:
            return False, "no USD stage (not running inside Isaac Sim)"
        handler = getattr(self, "_do_" + action.key.replace(".", "_"), None)
        if handler is None:
            return False, f"no handler for '{action.key}' yet (see Actions list)"
        try:
            return handler(action.params)
        except Exception as exc:  # never let one action kill the GUI
            return False, f"{action.key} failed: {exc}"

    # -- create ----------------------------------------------------------
    def _register(self, name: str, prim_path: str) -> str:
        base, i, final = name, 1, name
        while final in self.objects:
            i += 1
            final = f"{base}_{i}"
        self.objects[final] = prim_path
        return final

    def _do_create_objects_plane(self, p: dict) -> tuple:
        if not _CORE_OK:
            return False, "isaacsim.core.api unavailable"
        stage = _stage()
        self._ensure_world_root(stage)
        if stage.GetPrimAtPath("/World/GroundPlane").IsValid():
            return False, "a ground plane already exists (only one plane allowed)"
        name = self._register(p.get("name") or "ground_plane", "/World/GroundPlane")
        GroundPlane(prim_path="/World/GroundPlane", name=name, size=float(p.get("size") or 10.0))
        return True, f"plane '{name}' size={p.get('size')}"

    def _do_create_objects_cuboid(self, p: dict) -> tuple:
        if not _CORE_OK:
            return False, "isaacsim.core.api unavailable"
        stage = _stage()
        self._ensure_world_root(stage)
        name = p.get("name") or self._unique_name("create.objects.cuboid")
        prim_path = f"/World/{name}"
        if stage.GetPrimAtPath(prim_path).IsValid():
            return False, f"prim already exists: {prim_path}"
        pos = p.get("pos") or [0.0, 0.0, 0.5]
        size = float(p.get("size") if p.get("size") is not None else 1.0)
        color = p.get("color")
        DynamicCuboid(
            prim_path=prim_path,
            name=name,
            position=np.array(pos, dtype=np.float64),
            size=size,
            color=np.array(color, dtype=np.float64) if color else None,
        )
        mass = p.get("mass")
        if mass is not None:
            UsdPhysics.MassAPI.Apply(stage.GetPrimAtPath(prim_path)).CreateMassAttr(float(mass))
        self._apply_orient_scale(stage.GetPrimAtPath(prim_path), p)
        self._register(name, prim_path)
        return True, f"cuboid '{name}' size={size} pos={pos}"

    def _do_create_objects_sphere(self, p: dict) -> tuple:
        if not _CORE_OK:
            return False, "isaacsim.core.api unavailable"
        stage = _stage()
        self._ensure_world_root(stage)
        name = p.get("name") or self._unique_name("create.objects.sphere")
        prim_path = f"/World/{name}"
        if stage.GetPrimAtPath(prim_path).IsValid():
            return False, f"prim already exists: {prim_path}"
        pos = p.get("pos") or [0.0, 0.0, 0.5]
        radius = float(p.get("radius") if p.get("radius") is not None else 0.5)
        color = p.get("color")
        DynamicSphere(
            prim_path=prim_path,
            name=name,
            position=np.array(pos, dtype=np.float64),
            radius=radius,
            color=np.array(color, dtype=np.float64) if color else None,
        )
        mass = p.get("mass")
        if mass is not None:
            UsdPhysics.MassAPI.Apply(stage.GetPrimAtPath(prim_path)).CreateMassAttr(float(mass))
        self._apply_orient_scale(stage.GetPrimAtPath(prim_path), p)
        self._register(name, prim_path)
        return True, f"sphere '{name}' radius={radius} pos={pos}"

    # -- physics ---------------------------------------------------------
    def _prim(self, target: str):
        path = self.resolve_target(target)
        if path is None:
            return None, f"unknown target '{target}'"
        prim = _stage().GetPrimAtPath(path)
        if not prim.IsValid():
            return None, f"prim gone: {path}"
        return prim, ""

    def _do_physics_add_rigid_body(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("target") or "")
        if prim is None:
            return False, err
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            return False, f"'{p.get('target')}' is already rigid"
        UsdPhysics.RigidBodyAPI.Apply(prim)
        return True, f"'{p.get('target')}' is now rigid"

    def _do_physics_remove_rigid_body(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("target") or "")
        if prim is None:
            return False, err
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            return False, f"'{p.get('target')}' is not rigid"
        if not hasattr(prim, "RemoveAPI"):
            return False, "this USD build cannot remove API schemas"
        prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
        return True, f"'{p.get('target')}' is no longer rigid"

    def _do_physics_add_collider(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("target") or "")
        if prim is None:
            return False, err
        if not prim.IsA(UsdGeom.Gprim):
            return False, f"'{p.get('target')}' has no geometry for a collider"
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            return False, f"'{p.get('target')}' already has a collider"
        UsdPhysics.CollisionAPI.Apply(prim)
        return True, f"collider added to '{p.get('target')}'"

    def _do_physics_remove_collider(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("target") or "")
        if prim is None:
            return False, err
        if not prim.HasAPI(UsdPhysics.CollisionAPI):
            return False, f"'{p.get('target')}' has no collider"
        if not hasattr(prim, "RemoveAPI"):
            return False, "this USD build cannot remove API schemas"
        prim.RemoveAPI(UsdPhysics.CollisionAPI)
        return True, f"collider removed from '{p.get('target')}'"

    def _do_physics_set_mass(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("target") or "")
        if prim is None:
            return False, err
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            return False, f"'{p.get('target')}' is not rigid"
        UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(float(p.get("value") or 1.0))
        return True, f"mass of '{p.get('target')}' = {p.get('value')}"

    def _do_physics_set_pose(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("target") or "")
        if prim is None:
            return False, err
        pos, orient = p.get("pos"), p.get("orient")
        if pos is None and orient is None:
            return False, "need pos= and/or orient= (x,y,z,w)"
        xform = UsdGeom.Xformable(prim)
        if pos is not None:
            op = next(
                (o for o in xform.GetOrderedXformOps()
                 if o.GetOpType() == UsdGeom.XformOp.TypeTranslate),
                None,
            )
            if op is None:
                op = xform.AddTranslateOp()
            op.Set(Gf.Vec3f(*pos))
        if orient is not None:
            x, y, z, w = orient
            op = next(
                (o for o in xform.GetOrderedXformOps()
                 if o.GetOpType() == UsdGeom.XformOp.TypeOrient),
                None,
            )
            if op is None:
                op = xform.AddOrientOp()
            op.Set(Gf.Quatf(w, x, y, z))
        return True, f"pose of '{p.get('target')}' set"

    def _do_physics_set_velocity(self, p: dict) -> tuple:
        if not _PRIMS_OK:
            return False, "isaacsim.core.experimental unavailable"
        prim, err = self._prim(p.get("target") or "")
        if prim is None:
            return False, err
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            return False, f"'{p.get('target')}' is not rigid"
        linear, angular = p.get("linear"), p.get("angular")
        if linear is None and angular is None:
            return False, "need linear= and/or angular="
        if not self.is_playing():
            return False, "play the sim first (PhysX ignores pre-play velocity)"
        try:
            rp = RigidPrim(paths=str(prim.GetPath()))
            kw = {}
            if linear is not None:
                kw["linear_velocities"] = np.array([list(linear)])
            if angular is not None:
                kw["angular_velocities"] = np.array([list(angular)])
            rp.set_velocities(**kw)
        except Exception as exc:
            return False, f"set_velocities failed: {exc}"
        return True, f"velocity of '{p.get('target')}' set"

    # -- joints ----------------------------------------------------------
    def _do_joint_create_joint(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        from_path = self.resolve_target(p.get("from_prim") or "")
        to_path = self.resolve_target(p.get("to_prim") or "")
        if from_path is None:
            return False, f"unknown from_prim '{p.get('from_prim')}'"
        if to_path is None:
            return False, f"unknown to_prim '{p.get('to_prim')}'"
        if from_path == to_path:
            return False, "from_prim and to_prim must differ"
        stage = _stage()
        from_prim = stage.GetPrimAtPath(from_path)
        to_prim = stage.GetPrimAtPath(to_path)
        joint_type = p.get("joint_type") or "fixed"
        joints_root = "/World/Joints"
        if not stage.GetPrimAtPath(joints_root).IsValid():
            stage.DefinePrim(joints_root, "Xform")
        base = p.get("name") or f"{from_prim.GetName()}_to_{to_prim.GetName()}"
        safe = "".join(c if (c.isalnum() or c in "_-") else "_" for c in base)
        joint_path = f"{joints_root}/{safe}"
        if stage.GetPrimAtPath(joint_path).IsValid():
            return False, f"joint prim already exists: {joint_path}"
        joint = _joint_class(joint_type).Define(stage, joint_path)
        joint.CreateBody0Rel().SetTargets([Sdf.Path(from_path)])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(to_path)])
        # Joint frame at the to-body center, world-aligned: each side stores
        # the inverse of its body's world orientation, so jointing oriented
        # bodies (laid-down cylinder wheels) keeps the axis about world X/Y/Z.
        from_world = self._world_translate(from_prim)
        to_world = self._world_translate(to_prim)
        from_quat = self._world_orient(from_prim)
        to_quat = self._world_orient(to_prim)
        UsdGeom.Xformable(joint.GetPrim()).AddTranslateOp().Set(to_world)
        rot = Gf.Matrix4f()
        rot.SetRotate(from_quat.GetInverse())
        joint.CreateLocalPos0Attr(rot.TransformDir(Gf.Vec3f(to_world - from_world)))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
        joint.CreateLocalRot0Attr(from_quat.GetInverse())
        joint.CreateLocalRot1Attr(to_quat.GetInverse())
        if joint_type in ("revolute", "prismatic"):
            joint.CreateAxisAttr(p.get("axis") or "Z")
        name = self._register(p.get("name") or safe, joint_path)
        notes = [
            f"'{prim.GetName()}' not rigid"
            for prim in (from_prim, to_prim)
            if not prim.HasAPI(UsdPhysics.RigidBodyAPI)
        ]
        msg = f"{joint_type} joint '{name}' {from_path} -> {to_path}"
        if notes:
            msg += " (" + "; ".join(notes) + ")"
        return True, msg

    # -- robot -----------------------------------------------------------
    def _do_robot_add_articulation(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        path = self.resolve_target(p.get("path") or "")
        if path is None:
            return False, f"need path=<robot root prim> (got '{p.get('path')}')"
        prim = _stage().GetPrimAtPath(path)
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            return False, f"'{path}' is already an articulation root"
        UsdPhysics.ArticulationRootAPI.Apply(prim)
        msg = f"articulation root on '{path}'"
        if p.get("usd_path"):
            msg += " (usd_path assets not imported in v1)"
        return True, msg

    def _do_robot_set_joint_drive(self, p: dict) -> tuple:
        path = self.resolve_target(p.get("target") or "")
        if path is None:
            return False, f"unknown target '{p.get('target')}'"
        prim = _stage().GetPrimAtPath(path)
        concrete = (
            UsdPhysics.FixedJoint,
            UsdPhysics.RevoluteJoint,
            UsdPhysics.PrismaticJoint,
            UsdPhysics.SphericalJoint,
            UsdPhysics.DistanceJoint,
        )
        if not any(prim.IsA(cls) for cls in concrete):
            return False, f"'{path}' is not a joint"
        drive_type = "linear" if prim.IsA(UsdPhysics.PrismaticJoint) else "angular"
        drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
        stiffness = float(p.get("stiffness") or 0.0)
        damping = float(p.get("damping") or 0.0)
        max_force = float(p.get("max_force") or 0.0)
        drive.CreateStiffnessAttr(stiffness)
        drive.CreateDampingAttr(damping)
        drive.CreateMaxForceAttr(max_force)
        extras = ""
        if p.get("target_velocity") is not None:
            target_velocity = float(p["target_velocity"])
            drive.CreateTargetVelocityAttr(target_velocity)
            extras += f" vel={target_velocity}"
        if p.get("target_position") is not None:
            target_position = float(p["target_position"])
            drive.CreateTargetPositionAttr(target_position)
            extras += f" pos={target_position}"
        return True, f"{drive_type} drive on '{path}' k={stiffness} d={damping} fmax={max_force}{extras}"

    # -- materials -------------------------------------------------------
    def _do_material_add_rigid_body_material(self, p: dict) -> tuple:
        path = p.get("path")
        if not isinstance(path, str) or not path.startswith("/"):
            return False, f"path must be absolute, got '{path}'"
        stage = _stage()
        if stage.GetPrimAtPath(path).IsValid():
            return False, f"prim already exists: {path}"
        try:
            numbers = {
                key: float(p[key])
                for key in ("density", "staticFriction", "dynamicFriction", "restitution")
                if p.get(key) is not None
            }
        except (TypeError, ValueError):
            return False, "density/staticFriction/dynamicFriction/restitution must be numbers"
        material = UsdShade.Material.Define(stage, path)
        api = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
        if "density" in numbers:
            api.CreateDensityAttr(numbers["density"])
        if "staticFriction" in numbers:
            api.CreateStaticFrictionAttr(numbers["staticFriction"])
        if "dynamicFriction" in numbers:
            api.CreateDynamicFrictionAttr(numbers["dynamicFriction"])
        if "restitution" in numbers:
            api.CreateRestitutionAttr(numbers["restitution"])
        self._register(material.GetPrim().GetName(), path)
        shown = " ".join(f"{k}={v}" for k, v in numbers.items()) or "defaults"
        return True, f"physics material '{path}' ({shown})"

    def _do_material_bind_material(self, p: dict) -> tuple:
        target_path = self.resolve_target(p.get("prim_path") or "")
        material_path = self.resolve_target(p.get("material_path") or "")
        if target_path is None:
            return False, f"unknown prim '{p.get('prim_path')}'"
        if material_path is None:
            return False, f"unknown material '{p.get('material_path')}'"
        stage = _stage()
        material_prim = stage.GetPrimAtPath(material_path)
        if not material_prim.IsA(UsdShade.Material):
            return False, f"'{material_path}' is not a material"
        strength_raw = p.get("strength")
        if strength_raw in (None, "", "strong", "stronger", "strongerThanDescendants"):
            strength = UsdShade.Tokens.strongerThanDescendants
        elif strength_raw in ("weak", "weaker", "weakerThanDescendants"):
            strength = UsdShade.Tokens.weakerThanDescendants
        else:
            return False, f"strength must be strong/weak, got '{strength_raw}'"
        purpose_raw = p.get("material_purpose") or ""
        purpose = purpose_raw if purpose_raw else getattr(
            UsdShade.Tokens, "allPurpose", "allPurpose")
        binding = UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath(target_path))
        try:
            binding.Bind(UsdShade.Material(material_prim), strength, purpose)
        except TypeError:
            binding.Bind(UsdShade.Material(material_prim))
            return True, f"bound {material_path} -> {target_path} (default strength/purpose)"
        return True, f"bound {material_path} -> {target_path}"

    # -- sensors ---------------------------------------------------------
    def _do_sensor_create_rtx_lidar(self, p: dict) -> tuple:
        if not _LIDAR_OK:
            return False, "rtx sensor extension missing (enable isaacsim.sensors.experimental.rtx)"
        raw_path = p.get("path")
        if raw_path:
            path = raw_path if raw_path.startswith("/") else f"/World/{raw_path}"
            name = raw_path.rsplit("/", 1)[-1]
        else:
            name = self._unique_name("sensor.create.rtx_lidar")
            path = f"/World/{name}"
        stage = _stage()
        self._ensure_world_root(stage)
        if stage.GetPrimAtPath(path).IsValid():
            return False, f"prim already exists: {path}"
        kwargs = {}
        if p.get("tick_rate") is not None:
            kwargs["tick_rate"] = float(p["tick_rate"])
        Lidar(path, **kwargs)
        self._register(name, path)
        return True, f"rtx lidar '{name}' at {path}"

    # -- sim -------------------------------------------------------------
    def _do_sim_play(self, p: dict) -> tuple:
        if self.is_playing():
            return False, "already playing"
        world = self._get_world()
        if world is not None:
            world.play()
        else:
            _timeline().play()
        return True, "sim playing"

    def _do_sim_pause(self, p: dict) -> tuple:
        if not self.is_playing():
            return False, "not playing"
        world = self._get_world()
        if world is not None:
            world.pause()
        else:
            _timeline().pause()
        return True, "sim paused"

    def _do_sim_stop(self, p: dict) -> tuple:
        if not self.is_playing():
            return False, "not playing"
        world = self._get_world()
        if world is not None:
            world.stop()
        else:
            _timeline().stop()
        return True, "sim stopped"

    def _do_sim_step(self, p: dict) -> tuple:
        world = self._get_world()
        if world is None:
            return False, "step needs isaacsim World (unavailable)"
        n = int(p.get("n") or 1)
        resume = self.is_playing()
        if not resume:
            # World.step needs the physics context that play() creates.
            world.play()
        try:
            for _ in range(n):
                world.step(render=False)
        except Exception as exc:
            if not resume:
                try:
                    world.pause()
                except Exception:
                    pass
            return False, (f"sim.step failed: {exc} (needs a live physics "
                           "context; play the sim first so physics initializes)")
        if not resume:
            world.pause()
        return True, f"stepped {n} frame(s)"

    def _do_sim_reset(self, p: dict) -> tuple:
        world = self._get_world()
        if world is not None:
            world.reset()
            return True, "sim reset"
        _timeline().stop()
        _timeline().play()
        _timeline().pause()
        return True, "sim reset (timeline fallback)"

    # -- shared helpers --------------------------------------------------
    @staticmethod
    def _ensure_extension(name: str) -> tuple:
        """Enable an Isaac extension on demand -> (ok, msg)."""
        try:
            import isaacsim.core.experimental.utils.app as app_utils
        except Exception:
            return False, f"cannot enable {name} (core utils unavailable)"
        try:
            if app_utils.is_extension_enabled(name):
                return True, ""
            if app_utils.enable_extension(name):
                return True, ""
            return False, f"extension {name} could not be enabled"
        except Exception as exc:
            return False, f"extension {name} error: {exc}"

    def _as_joint(self, target: str):
        """Resolve a joint target -> (prim, path, err)."""
        path = self.resolve_target(target or "")
        if path is None:
            return None, "", f"unknown target '{target}'"
        prim = _stage().GetPrimAtPath(path)
        concrete = (
            UsdPhysics.FixedJoint,
            UsdPhysics.RevoluteJoint,
            UsdPhysics.PrismaticJoint,
            UsdPhysics.SphericalJoint,
            UsdPhysics.DistanceJoint,
        )
        if not any(prim.IsA(cls) for cls in concrete):
            return None, path, f"'{path}' is not a joint"
        return prim, path, ""

    @staticmethod
    def _parse_quat(raw, what: str = "orientation"):
        """'w,x,y,z' (parens ok) -> ([w,x,y,z], '') or (None, err)."""
        text = str(raw if raw is not None else "").strip()
        if not text:
            return None, ""
        if text.startswith("(") and text.endswith(")"):
            text = text[1:-1]
        parts = [q.strip() for q in text.split(",")]
        if len(parts) != 4:
            return None, f"{what} must be w,x,y,z (got '{raw}')"
        try:
            return [float(q) for q in parts], ""
        except ValueError:
            return None, f"{what} must be numbers (got '{raw}')"

    def _physics_scene_prim(self, create: bool = False):
        """Find the PhysicsScene prim, optionally creating it."""
        stage = _stage()
        probe = stage.GetPrimAtPath("/World/PhysicsScene")
        if probe.IsValid() and probe.GetTypeName() == "PhysicsScene":
            return probe, ""
        for prim in stage.Traverse():
            if prim.GetTypeName() == "PhysicsScene":
                return prim, ""
        if not create:
            return None, "no PhysicsScene on stage"
        self._ensure_world_root(stage)
        return stage.DefinePrim("/World/PhysicsScene", "PhysicsScene"), ""

    @staticmethod
    def _walk_articulation_root(prim):
        """Climb from prim to the nearest articulation root (or None)."""
        node = prim
        while node.IsValid():
            if node.HasAPI(UsdPhysics.ArticulationRootAPI):
                return node
            node = node.GetParent()
        return None

    @staticmethod
    def _set_drive_limit(prim, value: float, what: str) -> tuple:
        drive_type = "linear" if prim.IsA(UsdPhysics.PrismaticJoint) else "angular"
        drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
        drive.CreateMaxForceAttr(abs(float(value)))
        return True, f"{what} on '{prim.GetPath()}' maxForce={abs(float(value))}"

    # -- scene -----------------------------------------------------------
    def _do_scene_delete_prim(self, p: dict) -> tuple:
        target = p.get("target") or ""
        path = self.resolve_target(target)
        if path is None:
            return False, f"unknown target '{target}'"
        if path in ("/", "/World"):
            return False, "refusing to delete /World itself"
        _stage().RemovePrim(path)
        dropped = [n for n, pp in self.objects.items()
                   if pp == path or pp.startswith(path + "/")]
        for name in dropped:
            del self.objects[name]
        extra = f" (+{len(dropped)} registry entries)" if dropped else ""
        return True, f"deleted {path}{extra}"

    def _do_scene_create_prim(self, p: dict) -> tuple:
        raw_path = p.get("path")
        if not raw_path:
            return False, "need path=<prim path>"
        full = raw_path if raw_path.startswith("/") else f"/World/{raw_path}"
        stage = _stage()
        if stage.GetPrimAtPath(full).IsValid():
            return False, f"prim already exists: {full}"
        prim = stage.DefinePrim(full, p.get("type") or "Xform")
        if p.get("pos") is not None:
            UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3f(*p["pos"]))
        if p.get("scale") is not None:
            UsdGeom.Xformable(prim).AddScaleOp().Set(Gf.Vec3f(*p["scale"]))
        name = self._register(full.rstrip("/").rsplit("/", 1)[-1], full)
        return True, f"prim '{name}' ({prim.GetTypeName()}) at {full}"

    def _do_scene_save(self, p: dict) -> tuple:
        path = p.get("path")
        if path:
            try:
                ok = omni.usd.get_context().save_as_stage(path)
            except AttributeError:
                _stage().GetRootLayer().Export(path)
                return True, f"stage exported to {path}"
            except Exception as exc:
                return False, f"save failed: {exc}"
            return (True, f"stage saved to {path}") if ok else (False, f"save failed: {path}")
        try:
            _stage().Save()
        except Exception:
            return False, "stage has no file yet; pass path=<file.usd>"
        return True, "stage saved"

    def _do_scene_open(self, p: dict) -> tuple:
        path = p.get("path")
        if not path:
            return False, "need path=<usd file>"
        if not os.path.isfile(path):
            return False, f"file not found: {path}"
        ok, msg = self._ensure_extension("isaacsim.core.experimental.utils")
        if not ok:
            return False, msg
        try:
            from isaacsim.core.experimental.utils import stage as stage_utils

            future = asyncio.ensure_future(stage_utils.open_stage_async(path))
        except Exception as exc:
            return False, f"open failed: {exc}"

        def _done(fut):
            try:
                result = fut.result()
            except Exception:
                result = False
            if result:
                self.objects.clear()
                self._counters.clear()
                self._world = None
                self._world_failed = False

        future.add_done_callback(_done)
        return True, f"opening {path} (async; registry clears on success)"

    # -- physics scene ---------------------------------------------------
    def _do_physics_add_physics_scene(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        raw_path = p.get("path")
        if not raw_path:
            return False, "need path=<scene prim path>"
        full = raw_path if raw_path.startswith("/") else f"/World/{raw_path}"
        stage = _stage()
        if stage.GetPrimAtPath(full).IsValid():
            return False, f"prim already exists: {full}"
        stage.DefinePrim(full, "PhysicsScene")
        return True, f"physics scene at {full}"

    def _do_physics_set_rigid_body(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("path") or "")
        if prim is None:
            return False, err
        made = ""
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            UsdPhysics.RigidBodyAPI.Apply(prim)
            made = "made rigid; "
        if p.get("kinematic") is not None:
            prim.GetAttribute("physics:kinematicEnabled").Set(bool(p["kinematic"]))
        note = self._apply_approximation(prim, p.get("approximationShape"))
        return True, f"{made}rigid '{prim.GetPath()}' kinematic={bool(p.get('kinematic'))}{note}"

    def _do_physics_set_static_collider(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        prim, err = self._prim(p.get("path") or "")
        if prim is None:
            return False, err
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            return False, f"'{p.get('path')}' is rigid (remove rigid body first)"
        made = ""
        if not prim.HasAPI(UsdPhysics.CollisionAPI):
            UsdPhysics.CollisionAPI.Apply(prim)
            made = "collider added; "
        note = self._apply_approximation(prim, p.get("approximationShape"))
        return True, f"{made}static collider on '{prim.GetPath()}'{note}"

    @staticmethod
    def _apply_approximation(prim, raw) -> str:
        """Best-effort collision approximation for mesh prims."""
        name = str(raw or "none").strip()
        if name.lower() == "none":
            return ""
        mesh_api = getattr(UsdPhysics, "MeshCollisionAPI", None)
        if mesh_api is None or not prim.IsA(UsdGeom.Mesh):
            return f" (approximation '{name}' ignored: mesh-only)"
        known = {"convexhull": "convexHull", "convexdecomposition": "convexDecomposition",
                 "boundingsphere": "boundingSphere", "boundingcube": "boundingCube",
                 "meshsimplification": "meshSimplification"}
        token = known.get(name.lower())
        if token is None:
            return f" (unknown approximation '{name}' ignored)"
        try:
            mesh_api.Apply(prim).CreateApproximationAttr().Set(token)
        except Exception as exc:
            return f" (approximation failed: {exc})"
        return f" (approximation {token})"

    # -- sim tuning --------------------------------------------------------
    def _do_sim_set_gravity(self, p: dict) -> tuple:
        prim, err = self._physics_scene_prim(create=True)
        if prim is None:
            return False, err
        vec = p.get("value") or [0.0, 0.0, -9.81]
        mag = math.sqrt(sum(float(v) ** 2 for v in vec))
        scene = UsdPhysics.Scene(prim)
        if mag > 0:
            direction = [float(v) / mag for v in vec]
            scene.GetGravityDirectionAttr().Set(Gf.Vec3f(*direction))
        scene.GetGravityMagnitudeAttr().Set(float(mag))
        return True, f"gravity = {vec}"

    def _do_sim_set_dt(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        if not _PHYSX_SCHEMA_OK:
            return False, "PhysxSchema unavailable (physics dt needs it)"
        physics = p.get("physics")
        rendering = p.get("rendering")
        if physics is not None and float(physics) <= 0:
            return False, "physics dt must be > 0"
        if rendering is not None and float(rendering) <= 0:
            return False, "rendering dt must be > 0"
        prim, err = self._physics_scene_prim(create=True)
        if prim is None:
            return False, err
        try:
            PhysxSchema.PhysxSceneAPI.Apply(prim).GetTimeStepsPerSecondAttr().Set(
                1.0 / float(physics if physics is not None else 1.0 / 60.0))
        except AttributeError:
            return False, "PhysX build lacks timeStepsPerSecond"
        if rendering is not None:
            _stage().SetTimeCodesPerSecond(1.0 / float(rendering))
        return True, f"dt physics={physics} rendering={rendering}"

    # -- shapes (raw USD; no core.api needed) ----------------------------
    # dynamic = rigid + collider, fixed = static collider, visual = no physics.
    _SHAPE_MODE = {
        "create.objects.cylinder": ("cylinder", "dynamic"),
        "create.objects.cone": ("cone", "dynamic"),
        "create.objects.capsule": ("capsule", "dynamic"),
        "create.objects.fixed_cuboid": ("cuboid", "fixed"),
        "create.objects.fixed_sphere": ("sphere", "fixed"),
        "create.objects.fixed_cylinder": ("cylinder", "fixed"),
        "create.objects.fixed_cone": ("cone", "fixed"),
        "create.objects.fixed_capsule": ("capsule", "fixed"),
        "create.objects.visual_cuboid": ("cuboid", "visual"),
        "create.objects.visual_sphere": ("sphere", "visual"),
        "create.objects.visual_cylinder": ("cylinder", "visual"),
        "create.objects.visual_cone": ("cone", "visual"),
        "create.objects.visual_capsule": ("capsule", "visual"),
    }

    def _create_shape(self, key: str, p: dict) -> tuple:
        shape, mode = self._SHAPE_MODE[key]
        stage = _stage()
        self._ensure_world_root(stage)
        name = p.get("name") or self._unique_name(key)
        prim_path = f"/World/{name}"
        if stage.GetPrimAtPath(prim_path).IsValid():
            return False, f"prim already exists: {prim_path}"
        if shape == "cuboid":
            gprim = UsdGeom.Cube.Define(stage, prim_path)
            gprim.CreateSizeAttr(float(p.get("size") or 1.0))
        elif shape == "sphere":
            gprim = UsdGeom.Sphere.Define(stage, prim_path)
            gprim.CreateRadiusAttr(float(p.get("radius") or 0.5))
        elif shape == "cylinder":
            gprim = UsdGeom.Cylinder.Define(stage, prim_path)
            gprim.CreateRadiusAttr(float(p.get("radius") or 0.4))
            gprim.CreateHeightAttr(float(p.get("height") or 1.0))
        elif shape == "cone":
            gprim = UsdGeom.Cone.Define(stage, prim_path)
            gprim.CreateRadiusAttr(float(p.get("radius") or 0.4))
            gprim.CreateHeightAttr(float(p.get("height") or 1.0))
        elif shape == "capsule":
            capsule_cls = getattr(UsdGeom, "Capsule", None)
            if capsule_cls is None:
                return False, "this USD build has no Capsule schema"
            gprim = capsule_cls.Define(stage, prim_path)
            gprim.CreateRadiusAttr(float(p.get("radius") or 0.3))
            gprim.CreateHeightAttr(float(p.get("height") or 1.0))
        else:  # pragma: no cover - table-driven
            return False, f"unknown shape '{shape}'"
        prim = stage.GetPrimAtPath(prim_path)
        pos = p.get("pos") or [0.0, 0.0, 0.5]
        UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3f(*pos))
        self._apply_orient_scale(prim, p)
        color = p.get("color")
        if color:
            gprim.GetDisplayColorAttr().Set([Gf.Vec3f(*color)])
        if mode in ("dynamic", "fixed"):
            UsdPhysics.CollisionAPI.Apply(prim)
        if mode == "dynamic":
            UsdPhysics.RigidBodyAPI.Apply(prim)
            if p.get("mass") is not None:
                UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(float(p["mass"]))
        self._register(name, prim_path)
        return True, f"{mode} {shape} '{name}' at {prim_path}"

    def _do_create_objects_cylinder(self, p: dict) -> tuple:
        return self._create_shape("create.objects.cylinder", p)

    def _do_create_objects_cone(self, p: dict) -> tuple:
        return self._create_shape("create.objects.cone", p)

    def _do_create_objects_capsule(self, p: dict) -> tuple:
        return self._create_shape("create.objects.capsule", p)

    def _do_create_objects_fixed_cuboid(self, p: dict) -> tuple:
        return self._create_shape("create.objects.fixed_cuboid", p)

    def _do_create_objects_fixed_sphere(self, p: dict) -> tuple:
        return self._create_shape("create.objects.fixed_sphere", p)

    def _do_create_objects_fixed_cylinder(self, p: dict) -> tuple:
        return self._create_shape("create.objects.fixed_cylinder", p)

    def _do_create_objects_fixed_cone(self, p: dict) -> tuple:
        return self._create_shape("create.objects.fixed_cone", p)

    def _do_create_objects_fixed_capsule(self, p: dict) -> tuple:
        return self._create_shape("create.objects.fixed_capsule", p)

    def _do_create_objects_visual_cuboid(self, p: dict) -> tuple:
        return self._create_shape("create.objects.visual_cuboid", p)

    def _do_create_objects_visual_sphere(self, p: dict) -> tuple:
        return self._create_shape("create.objects.visual_sphere", p)

    def _do_create_objects_visual_cylinder(self, p: dict) -> tuple:
        return self._create_shape("create.objects.visual_cylinder", p)

    def _do_create_objects_visual_cone(self, p: dict) -> tuple:
        return self._create_shape("create.objects.visual_cone", p)

    def _do_create_objects_visual_capsule(self, p: dict) -> tuple:
        return self._create_shape("create.objects.visual_capsule", p)

    # -- import / export -------------------------------------------------
    def _reference_usd(self, usd_file: str, name: str):
        """Reference a USD file under /World -> (prim_path, err)."""
        stage = _stage()
        self._ensure_world_root(stage)
        prim_path = f"/World/{name}"
        if stage.GetPrimAtPath(prim_path).IsValid():
            return "", f"prim already exists: {prim_path}"
        prim = stage.DefinePrim(prim_path, "Xform")
        prim.GetReferences().AddReference(usd_file)
        return prim_path, ""

    def _do_import_robot_urdf(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        path = p.get("path") or ""
        if not os.path.isfile(path):
            return False, f"file not found: {path}"
        if not path.lower().endswith(".urdf"):
            return False, f"not a .urdf file: {path}"
        ok, msg = self._ensure_extension("isaacsim.asset.importer.urdf")
        if not ok:
            return False, msg
        from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig

        config = URDFImporterConfig(
            urdf_path=path,
            fix_base=bool(p.get("fix_base")),
            merge_fixed_joints=bool(p.get("merge_fixed_joints", True)),
        )
        importer = URDFImporter()
        importer.config = config
        final_usd = importer.import_urdf()
        robot = os.path.splitext(os.path.basename(path))[0].replace(" ", "_")
        prim_path, err = self._reference_usd(final_usd, robot)
        if err:
            return False, f"converted to {final_usd} but {err}"
        name = self._register(robot, prim_path)
        return True, f"urdf '{name}' -> {prim_path} (usd: {final_usd})"

    def _do_import_robot_mjcf(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        path = p.get("path") or ""
        if not os.path.isfile(path):
            return False, f"file not found: {path}"
        if not path.lower().endswith((".xml", ".mjcf")):
            return False, f"not a MJCF file (.xml/.mjcf): {path}"
        ok, msg = self._ensure_extension("isaacsim.asset.importer.mjcf")
        if not ok:
            return False, msg
        from isaacsim.asset.importer.mjcf import MJCFImporter, MJCFImporterConfig

        importer = MJCFImporter()
        importer.config = MJCFImporterConfig(mjcf_path=path)
        final_usd = importer.import_mjcf()
        robot = os.path.splitext(os.path.basename(path))[0].replace(" ", "_")
        prim_path, err = self._reference_usd(final_usd, robot)
        if err:
            return False, f"converted to {final_usd} but {err}"
        name = self._register(robot, prim_path)
        return True, f"mjcf '{name}' -> {prim_path} (usd: {final_usd})"

    def _do_import_asset_usd(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        path = p.get("path") or ""
        if not os.path.isfile(path):
            return False, f"file not found: {path}"
        if not path.lower().endswith((".usd", ".usda", ".usdc", ".usdz")):
            return False, f"not a USD file: {path}"
        name = (p.get("name") or
                os.path.splitext(os.path.basename(path))[0]).replace(" ", "_")
        prim_path, err = self._reference_usd(path, name)
        if err:
            return False, err
        if p.get("pos") is not None:
            prim = _stage().GetPrimAtPath(prim_path)
            UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3f(*p["pos"]))
        name = self._register(name, prim_path)
        return True, f"usd '{name}' -> {prim_path}"

    def _do_import_asset_heightmap(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        path = p.get("path") or ""
        if not os.path.isfile(path):
            return False, f"file not found: {path}"
        ok, msg = self._ensure_extension("isaacsim.asset.importer.heightmap")
        if not ok:
            return False, msg
        try:
            from PIL import Image
        except Exception:
            return False, "PIL unavailable (heightmap needs it)"
        try:
            image = Image.open(path)
        except Exception as exc:
            return False, f"cannot open image {path}: {exc}"
        from isaacsim.asset.importer.heightmap.importer import HeightmapImporter

        count = HeightmapImporter(_stage()).create_heightmap(
            image, float(p.get("scale") or 1.0),
            create_ground_plane=False, create_lighting=False)
        return True, f"heightmap: {count} terrain instances (scale={p.get('scale')})"

    def _do_export_asset_urdf(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        out = p.get("path") or ""
        if not out:
            return False, "need path=<output.urdf>"
        ok, msg = self._ensure_extension("isaacsim.asset.exporter.urdf")
        if not ok:
            return False, msg
        stage = _stage()
        root = None
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                root = prim
                break
        if root is None:
            return False, "no articulation root on stage (build or import a robot first)"
        from isaacsim.asset.exporter.urdf import UsdToUrdfConverter

        result = UsdToUrdfConverter(stage, root_prim_path=str(root.GetPath())).convert(out)
        return True, f"exported {root.GetPath()} -> {result}"

    # -- robot drives ----------------------------------------------------
    def _do_robot_set_torque(self, p: dict) -> tuple:
        prim, _, err = self._as_joint(p.get("target") or "")
        if prim is None:
            return False, err
        ok, msg = self._set_drive_limit(prim, p.get("value") or 0.0, "torque capacity")
        return ok, msg + " (pair with target_velocity to spin)"

    def _do_robot_set_torque_limit(self, p: dict) -> tuple:
        prim, _, err = self._as_joint(p.get("target") or "")
        if prim is None:
            return False, err
        return self._set_drive_limit(prim, p.get("value") or 0.0, "torque limit")

    def _do_robot_set_velocity_limit(self, p: dict) -> tuple:
        prim_path = self.resolve_target(p.get("target") or "")
        if prim_path is None:
            return False, f"unknown target '{p.get('target')}'"
        if not _PHYSX_SCHEMA_OK:
            return False, "PhysxSchema unavailable (velocity limit needs it)"
        root = self._walk_articulation_root(_stage().GetPrimAtPath(prim_path))
        if root is None:
            return False, "no articulation root above target (add articulation first)"
        api = PhysxSchema.PhysxArticulationAPI.Apply(root)
        setter = getattr(api, "CreateMaxJointVelocityAttr", None)
        if setter is None:
            return False, "PhysX build lacks maxJointVelocity"
        setter(float(p.get("value") or 0.0))
        return True, f"velocity limit {p.get('value')} rad/s on '{root.GetPath()}'"

    def _do_robot_clone(self, p: dict) -> tuple:
        ok, msg = self._need_paused()
        if not ok:
            return False, msg
        path = self.resolve_target(p.get("target") or "")
        if path is None:
            return False, f"unknown target '{p.get('target')}'"
        count = int(p.get("count") or 1)
        stage = _stage()
        src_layer = None
        for layer in (stage.GetEditTarget().GetLayer(), stage.GetRootLayer(),
                      stage.GetSessionLayer()):
            try:
                if layer and layer.GetPrimAtPath(path):
                    src_layer = layer
                    break
            except Exception:
                continue
        if src_layer is None:
            return False, f"cannot copy {path} (spec not in editable layers)"
        made = []
        for i in range(1, count + 1):
            dst, attempt = f"{path}_clone{i}", 0
            while stage.GetPrimAtPath(dst).IsValid() and attempt < 100:
                attempt += 1
                dst = f"{path}_clone{i}_{attempt}"
            if stage.GetPrimAtPath(dst).IsValid():
                return False, f"no free path for clone {i}"
            Sdf.CopySpec(src_layer, Sdf.Path(path),
                         stage.GetEditTarget().GetLayer(), Sdf.Path(dst))
            clone = stage.GetPrimAtPath(dst)
            op = next((o for o in UsdGeom.Xformable(clone).GetOrderedXformOps()
                       if o.GetOpType() == UsdGeom.XformOp.TypeTranslate), None)
            offset = Gf.Vec3f(i * 2.0, 0, 0)
            if op is None:
                UsdGeom.Xformable(clone).AddTranslateOp().Set(offset)
            else:
                op.Set(Gf.Vec3f(op.Get()) + offset)
            made.append(self._register(dst.rsplit("/", 1)[-1], dst))
        return True, (f"cloned {len(made)}: {', '.join(made)} "
                      "(joints inside clones keep original targets)")

    # -- rtx sensors -----------------------------------------------------
    def _rtx_path(self, key: str, p: dict):
        """Resolve base/parent + name -> (full_path, name, err)."""
        parent = p.get("parent")
        if parent:
            base = self.resolve_target(parent)
            if base is None:
                return "", "", f"unknown parent '{parent}'"
        else:
            base = "/World"
        raw_path = p.get("path")
        if raw_path:
            full = raw_path if raw_path.startswith("/") else f"{base}/{raw_path}"
            name = raw_path.rsplit("/", 1)[-1]
        else:
            name = self._unique_name(key)
            full = f"{base}/{name}"
        if _stage().GetPrimAtPath(full).IsValid():
            return "", "", f"prim already exists: {full}"
        return full, name, ""

    def _rtx_pose_kwargs(self, p: dict):
        """translation/orientation/tick_rate -> (kwargs, err)."""
        quat, err = self._parse_quat(p.get("orientation"), "orientation")
        if err:
            return None, err
        kwargs = {}
        if p.get("translation") is not None:
            kwargs["translations"] = [list(p["translation"])]
        if quat is not None:
            kwargs["orientations"] = [quat]
        if p.get("tick_rate") is not None:
            kwargs["tick_rate"] = float(p["tick_rate"])
        return kwargs, ""

    def _do_sensor_create_rtx_radar(self, p: dict) -> tuple:
        ok, msg = self._ensure_extension("isaacsim.sensors.experimental.rtx")
        if not ok:
            return False, msg
        try:
            carb.settings.get_settings().set("/renderer/raytracingMotion/enabled", True)
        except Exception:
            pass  # Radar raises a clear error if Motion BVH stays off
        from isaacsim.sensors.experimental.rtx import Radar

        full, name, err = self._rtx_path("sensor.create.rtx_radar", p)
        if err:
            return False, err
        kwargs, err = self._rtx_pose_kwargs(p)
        if err:
            return False, err
        Radar(full, **kwargs)
        self._register(name, full)
        return True, f"rtx radar '{name}' at {full} (config/variant unused)"

    def _do_sensor_create_rtx_ultrasonic(self, p: dict) -> tuple:
        ok, msg = self._ensure_extension("isaacsim.sensors.experimental.rtx")
        if not ok:
            return False, msg
        from isaacsim.sensors.experimental.rtx import Acoustic

        full, name, err = self._rtx_path("sensor.create.rtx_ultrasonic", p)
        if err:
            return False, err
        kwargs, err = self._rtx_pose_kwargs(p)
        if err:
            return False, err
        Acoustic(full, **kwargs)
        self._register(name, full)
        return True, f"rtx ultrasonic '{name}' at {full} (config/variant unused)"

    # -- physics raycast sensors -------------------------------------------
    @staticmethod
    def _raycast_class():
        try:
            from isaacsim.sensors.experimental.physics import Raycast

            return Raycast
        except ImportError:
            from isaacsim.sensors.experimental.physics.impl.raycast import Raycast

            return Raycast

    def _do_sensor_do_range_sensor_create_generic(self, p: dict) -> tuple:
        ok, msg = self._ensure_extension("isaacsim.sensors.experimental.physics")
        if not ok:
            return False, msg
        full, name, err = self._rtx_path("sensor.do.range_sensor_create_generic", p)
        if err:
            return False, err
        kwargs, err = self._rtx_pose_kwargs(p)
        if err:
            return False, err
        raycast_cls = self._raycast_class()
        raycast_cls(
            full,
            min_range=p.get("min_range"),
            max_range=p.get("max_range"),
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            **kwargs,
        )
        self._register(name, full)
        return True, (f"range sensor '{name}' at {full} "
                      "(single +X ray; draw/sampling unused)")

    def _do_sensor_do_range_sensor_create_lidar(self, p: dict) -> tuple:
        ok, msg = self._ensure_extension("isaacsim.sensors.experimental.physics")
        if not ok:
            return False, msg
        full, name, err = self._rtx_path("sensor.do.range_sensor_create_lidar", p)
        if err:
            return False, err
        kwargs, err = self._rtx_pose_kwargs(p)
        if err:
            return False, err
        hfov = float(p.get("horizontal_fov") if p.get("horizontal_fov") is not None else 360.0)
        vfov = float(p.get("vertical_fov") if p.get("vertical_fov") is not None else 30.0)
        hres = float(p.get("horizontal_resolution") or 0.4)
        vres = float(p.get("vertical_resolution") or 4.0)
        if hres <= 0 or vres <= 0:
            return False, "resolutions must be > 0"
        note = ""
        while max(1, round(hfov / hres)) * max(1, round(vfov / vres)) > 8192:
            hres *= 2.0
            vres *= 2.0
            note = f" (coarsened to hres={hres} vres={vres} for the 8192-ray cap)"
        nh, nv = max(1, round(hfov / hres)), max(1, round(vfov / vres))
        yaw0 = float(p.get("yaw_offset") or 0.0) - hfov / 2.0
        origins, directions = [], []
        for j in range(nv):
            pitch = math.radians(-vfov / 2.0 + (vfov * j / max(nv - 1, 1)))
            for i in range(nh):
                yaw = math.radians(yaw0 + (hfov * i / max(nh - 1, 1)))
                origins.append([0.0, 0.0, 0.0])
                directions.append([math.cos(pitch) * math.cos(yaw),
                                   math.cos(pitch) * math.sin(yaw),
                                   math.sin(pitch)])
        raycast_cls = self._raycast_class()
        raycast_cls(
            full,
            min_range=p.get("min_range"),
            max_range=p.get("max_range"),
            ray_origins=origins,
            ray_directions=directions,
            **kwargs,
        )
        self._register(name, full)
        return True, f"raycast lidar '{name}' at {full} ({nh * nv} rays){note}"

    def _do_sensor_create_light_beam_sensor(self, p: dict) -> tuple:
        ok, msg = self._ensure_extension("isaacsim.sensors.experimental.physics")
        if not ok:
            return False, msg
        full, name, err = self._rtx_path("sensor.create.light_beam_sensor", p)
        if err:
            return False, err
        kwargs, err = self._rtx_pose_kwargs(p)
        if err:
            return False, err
        nrays = int(p.get("num_rays") or 1)
        if nrays < 1:
            return False, "num_rays must be >= 1"
        if nrays > 1024:
            return False, "num_rays capped at 1024"
        fwd = [float(v) for v in (p.get("forward_axis") or [1.0, 0.0, 0.0])]
        axis = [float(v) for v in (p.get("curtain_axis") or [0.0, 0.0, 1.0])]
        if math.sqrt(sum(v * v for v in fwd)) == 0:
            return False, "forward_axis must be non-zero"
        length = float(p.get("curtain_length") or 0.0)
        origins = [[axis[k] * (length * (i - (nrays - 1) / 2.0) / max(nrays - 1, 1))
                    for k in range(3)] for i in range(nrays)]
        raycast_cls = self._raycast_class()
        raycast_cls(
            full,
            min_range=p.get("min_range"),
            max_range=p.get("max_range"),
            ray_origins=origins,
            ray_directions=[fwd] * nrays,
            **kwargs,
        )
        self._register(name, full)
        return True, f"light beam '{name}' at {full} ({nrays} rays)"

    # -- observer (telemetry seed for the Thinker) ------------------------
    def snapshot(self, max_prims: int = 200, max_depth: int = 6) -> str:
        if not _USD_OK:
            return "no USD stage (not running inside Isaac Sim)"
        stage = _stage()
        root = stage.GetPrimAtPath("/World")
        if not root.IsValid():
            return "stage has no /World"
        lines = [f"sim: {'playing' if self.is_playing() else 'paused'}{_timeline_info()}"]
        count = 0
        stack = [(root, 0)]
        while stack and count < max_prims:
            prim, depth = stack.pop()
            if depth > 0:
                flags = (
                    ("R" if prim.HasAPI(UsdPhysics.RigidBodyAPI) else "-")
                    + ("C" if prim.HasAPI(UsdPhysics.CollisionAPI) else "-")
                    + ("A" if prim.HasAPI(UsdPhysics.ArticulationRootAPI) else "-")
                )
                entry = f"[{flags}] {prim.GetPath()} ({prim.GetTypeName()})"
                if "R" in flags:
                    try:
                        pos = self._world_translate(prim)
                        entry += f" pos={pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f}"
                    except Exception:
                        pass
                lines.append(entry)
                count += 1
            if depth < max_depth:
                stack.extend((c, depth + 1) for c in reversed(list(prim.GetChildren())))
        if stack:
            lines.append(f"... truncated at {max_prims} prims")
        if self.objects:
            lines.append("registry:")
            lines.extend(f"  {name} -> {path}" for name, path in self.objects.items())
        return "\n".join(lines)
