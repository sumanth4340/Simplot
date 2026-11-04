"""P4 URDF probe (runs INSIDE Isaac Sim): run URDF profile, list tree."""
import os
import shutil
import isaacsim.core.experimental.utils.app as app_utils
app_utils.enable_extension("isaacsim.asset.importer.urdf")
from isaacsim.asset.transformer import (
    AssetTransformerManager, RuleProfile)

EVD = "C:/Users/sruja_ob3di74/action-reasoner/skills/physics/engines/evidence/p4_probe"
shutil.rmtree(EVD, ignore_errors=True)
os.makedirs(EVD, exist_ok=True)
URDF = EVD + "/p4_min.urdf"
open(URDF, "w").write("""<robot name="p4arm">
  <link name="world"/>
  <link name="base">
    <inertial><mass value="1.0"/>
      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/></inertial>
    <visual><geometry><box size="0.1 0.1 0.1"/></geometry></visual>
    <collision><geometry><box size="0.1 0.1 0.1"/></geometry></collision>
  </link>
  <link name="l1">
    <inertial><mass value="1.0"/>
      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/></inertial>
    <visual><geometry><box size="0.1 0.1 0.1"/></geometry></visual>
    <collision><geometry><box size="0.1 0.1 0.1"/></geometry></collision>
  </link>
  <joint name="root_fixed" type="fixed">
    <parent link="world"/><child link="base"/>
    <origin xyz="0 0 0" rpy="0 0 0"/>
  </joint>
  <joint name="j1" type="revolute">
    <parent link="base"/><child link="l1"/>
    <origin xyz="0 0 0.2" rpy="0 0 0"/><axis xyz="0 1 0"/>
    <limit lower="-1.57" upper="1.57" effort="10" velocity="2"/>
    <dynamics damping="1.0" friction="0.0"/>
  </joint>
</robot>
""")
rules_path = app_utils.get_extension_path(
    "isaacsim.asset.transformer.rules")
with open(os.path.join(rules_path, "data",
                       "urdf_to_mjc_physx_conversion.json"),
          encoding="utf-8") as f:
    profile = RuleProfile.from_json(f.read())
OUT = EVD + "/out"
os.makedirs(OUT, exist_ok=True)
report = AssetTransformerManager().run(
    input_stage=URDF, profile=profile, package_root=OUT)
tree = []
for dp, _, fns in os.walk(OUT):
    tree += [os.path.relpath(os.path.join(dp, x), OUT) for x in fns]
print("P4-PROBE rules=%d ok=%s files=%s" % (
    len(report.results),
    all(r.success for r in report.results),
    sorted(tree)))
for r in report.results:
    if not r.success:
        print("FAIL-RULE %s: %s" % (r.rule.name, r.error))
