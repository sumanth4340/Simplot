"""M2 import (runs INSIDE Isaac Sim): URDF 2-link arm -> USD -> reference.

import_urdf() converts offline to a USD package (live stage untouched);
the drill then references the package root at /World/M2Bot. Scopes:
Geometry/<link> visuals, Physics/<joint> joints.
"""
import os
import omni.usd
from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig

BASE = "C:/Users/sruja_ob3di74/action-reasoner/skills/modeling-assets/assets"
config = URDFImporterConfig(
    urdf_path=os.path.normpath(BASE + "/m2_bot.urdf"),
    usd_path=os.path.normpath(BASE + "/m2_out"),
)
out = URDFImporter(config).import_urdf()
stage = omni.usd.get_context().get_stage()
ref = stage.DefinePrim("/World/M2Bot")
ref.GetReferences().AddReference(out)
root = stage.GetPrimAtPath("/World/M2Bot")
joints = [str(p.GetPath()) for p in stage.Traverse()
          if "Joint" in p.GetTypeName()]
links = ["/World/M2Bot/Geometry/base", "/World/M2Bot/Geometry/base/arm"]
print("M2-REPORT out=%s root=%s joints=%s base=%s arm=%s"
      % (out, root.IsValid(), ",".join(sorted(joints)),
         stage.GetPrimAtPath(links[0]).IsValid(),
         stage.GetPrimAtPath(links[1]).IsValid()))
