# sensors — Discovery Notes (live-verified)

---

# Part: base (merged from `sensors`)

# Sensors — Discovery Notes (live-verified, Isaac Sim 6.0.0)

## Camera AOVs (CameraSensor.get_data — the documented path)
- Multi-annotator attach works: ["rgb", "distance_to_image_plane"].
- Depth shape is (H,W,1), not (H,W). Center-ray depth is EXACT:
  predicted 3.738, measured 3.738.
- Focal-24 FOV is narrow: 1m cube at 3.7m fills the frame.

## RTX LiDAR (Lidar.create + Writer-based GMO)
- ALWAYS consume GMO via a Writer (skill rule); get_data polling
  drops/dupes under multitick.
- PROVEN: Example_Rotary GMO (x,y,z) = (azimuth_deg, elevation_deg,
  range_m) - spherical. Cartesian assumption yields a "phantom ring"
  (rmin=12.022 across 7 runs). Spherical map validates 100.0% on the
  known cube top. Validate the mapping against known geometry FIRST.
- Author/move RTX sensors while STOPPED; live moves/creates emit
  nothing until a stop/play re-parse (R5).
- Lidar.create positions kwarg applies correctly (0,0,1.5 confirmed).
- nearRangeM=1.0/farRangeM=200 conf; 128ch, el -15..+10.
- OPEN (R6): wedge never sweeps (24/24 identical frames) + zero
  ground returns. Full-surround scans blocked on this.

## Physics sensors (installed API drifts from skill sketches)
- IMU.create(path) - no tick_rate kwarg; IMUSensor(path) - no
  annotators kwarg; get_data(read_gravity=True) -> dict. Resting
  cube: accel [0,0,9.81] exact, angvel 0, orient identity.
- Contact.create(path, min/max/radius) valid; ContactSensor(path);
  get_data() -> in_contact/force/time/physics_step/
  number_of_contacts. Resting contact needs: scene disableSleeping
  (sleeping pairs emit NOTHING - R7) + PhysxContactReportAPI@0.0 on
  the sensed body + sensor as DIRECT child of the rigid body.
  Proven: 1kg -> 9.8098N n=4; 2kg -> 19.6201N.
- Contact first read can be partial (R8): prime after play + retry
  until 'in_contact' present.
- Probe installed signatures first (Skill 6 R3 rule, again).

## Stage facts
- Virgin boot has /Environment/defaultLight (DistantLight 3000.0) -
  prime suspect for the Skill 6 R5 ambient floor (~95pts @ dome=0).
- No /PhysicsScene at boot; drills define their own.

radac (`radac`) shipped no discovery.md; its notes live in SKILL.md.
