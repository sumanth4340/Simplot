# Workspace Sense — Failure Catalog (live-verified)

## V1: purpose="render" prims invisible to ["default"] bbox query
- FAILURE: S3 cube (purpose set to "render") sensed bbox ±FLT_MAX (empty).
- CAUSE: `BBoxCache(time, ["default"])` excludes explicit "render"/"proxy"
  purpose prims.
- RECOVERY: Query purposes ["default", "render", "proxy"]; "guide" stays
  excluded (guides are not physical). Probe v0.4.
- PREVENTION: Co-drills must cover non-default purposes (S3 does).
