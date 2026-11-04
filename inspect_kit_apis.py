"""Read-only Kit/USD API introspection. Run: C:\\isaacsim\\python.bat action-reasoner/inspect_kit_apis.py"""
import inspect


def check(label, obj, attrs):
    missing = [a for a in attrs if not hasattr(obj, a)]
    status = "OK  " if not missing else "MISS"
    print(f"{status} {label}: missing={missing or '-'}", flush=True)


print("== pxr.UsdPhysics ==", flush=True)
from pxr import Gf, UsdGeom, UsdPhysics, UsdShade

for joint in ["FixedJoint", "RevoluteJoint", "PrismaticJoint", "SphericalJoint", "DistanceJoint"]:
    print(("OK   " if hasattr(UsdPhysics, joint) else "MISS ") + f"UsdPhysics.{joint}", flush=True)
check("RevoluteJoint", UsdPhysics.RevoluteJoint,
      ["Define", "CreateAxisAttr", "CreateBody0Rel", "CreateBody1Rel",
       "CreateLocalPos0Attr", "CreateLocalPos1Attr", "CreateLocalRot0Attr", "CreateLocalRot1Attr"])
check("DriveAPI", UsdPhysics.DriveAPI,
      ["Apply", "CreateStiffnessAttr", "CreateDampingAttr", "CreateMaxForceAttr",
       "CreateTargetPositionAttr", "CreateTargetVelocityAttr"])
check("MassAPI", UsdPhysics.MassAPI, ["Apply", "CreateMassAttr"])
check("ArticulationRootAPI", UsdPhysics.ArticulationRootAPI, ["Apply"])
check("MaterialAPI", UsdPhysics.MaterialAPI,
      ["Apply", "CreateDensityAttr", "CreateStaticFrictionAttr",
       "CreateDynamicFrictionAttr", "CreateRestitutionAttr"])
check("RigidBodyAPI", UsdPhysics.RigidBodyAPI, ["Apply"])
check("CollisionAPI", UsdPhysics.CollisionAPI, ["Apply"])

print("== UsdPrim ==", flush=True)
from pxr import Usd

print(("OK   " if hasattr(Usd.Prim, "RemoveAPI") else "MISS ") + "Usd.Prim.RemoveAPI", flush=True)
print(("OK   " if hasattr(Usd.Prim, "HasAPI") else "MISS ") + "Usd.Prim.HasAPI", flush=True)

print("== UsdShade ==", flush=True)
check("Material", UsdShade.Material, ["Define", "GetPath"])
try:
    print(f"OK   MaterialBindingAPI.Bind{inspect.signature(UsdShade.MaterialBindingAPI.Bind)}", flush=True)
except Exception as e:
    print(f"FAIL MaterialBindingAPI.Bind: {e}", flush=True)

print("== UsdGeom ==", flush=True)
check("Xformable", UsdGeom.Xformable,
      ["GetOrderedXformOps", "AddTranslateOp", "AddOrientOp"])

print("== PhysxSchema ==", flush=True)
try:
    from pxr import PhysxSchema

    check("PhysxRigidBodyAPI", PhysxSchema.PhysxRigidBodyAPI,
          ["Apply", "CreateVelocityAttr", "CreateAngularVelocityAttr"])
except Exception as e:
    print(f"FAIL PhysxSchema import: {e}", flush=True)

print("== isaacsim.core.api ==", flush=True)
try:
    from isaacsim.core.api.objects import DynamicCuboid, DynamicSphere, GroundPlane

    for cls in (GroundPlane, DynamicCuboid, DynamicSphere):
        try:
            print(f"OK   {cls.__name__}{inspect.signature(cls.__init__)}", flush=True)
        except Exception as e:
            print(f"FAIL {cls.__name__} sig: {e}", flush=True)
except Exception as e:
    print(f"FAIL objects import: {e}", flush=True)
try:
    from isaacsim.core.api.world import World

    check("World", World, ["play", "pause", "stop", "step", "reset"])
    print(("OK   " if hasattr(World, "instance") else "MISS ") + "World.instance", flush=True)
except Exception as e:
    print(f"FAIL World import: {e}", flush=True)

print("== omni.kit.commands registry ==", flush=True)
try:
    import omni.kit.commands

    names = []
    for getter in ("get_command_list", "get_registered_commands", "list_commands"):
        if hasattr(omni.kit.commands, getter):
            names = list(getattr(omni.kit.commands, getter)())
            print(f"OK   via {getter}: {len(names)} commands", flush=True)
            break
    interesting = [n for n in names
                   if any(k in str(n).lower() for k in ("lidar", "rtx", "range", "joint", "material"))]
    print("interesting:", interesting[:30] or "(none found)", flush=True)
except Exception as e:
    print(f"FAIL commands registry: {e}", flush=True)

print("== omni.physx.utils ==", flush=True)
try:
    import omni.physx.utils

    check("physx.utils", omni.physx.utils, ["createJoint", "addRigidBodyMaterial"])
except Exception as e:
    print(f"FAIL physx.utils import: {e}", flush=True)
