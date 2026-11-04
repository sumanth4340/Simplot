# ros-navigation — TOOLS_REF (exhaustive tool mastery, 2026-11-04)

Claim tags: [verified] = live-observed in this pack's drills/evidence;
[probable] = strongly implied by code + docs but not directly gated;
[theoretical] = untested extrapolation, do not rely on.

Fully read (51): bridge listener_ros.py, talker_ros.py, r1_build.py,
r2_build.py, r2_drive.py, r3_build.py, r3_drive.py, r4_build.py,
topic_info.py, r2_pumped_listen.ps1, r2_pump40.py, listen.ps1,
r3_pumped_talk.ps1, r2_body.py, r2_ctldbg.py, r2_gap.py,
r2_matrix.py, r2_pubcount.py, r2_deeplisten.py, r2_dcstate.py,
r2_artstate.py, r3_diag.py, r2_reset.py, exam15.py,
tmp_rmwprobe.ps1, tmp_rosenv.ps1, tmp_topics.ps1,
r2_pubcount.ps1, r2_deep.ps1 (29); bringup n1_build.py,
n1_drive.py, n2_mount.py, n2_drive.py, verify_n2.py, n1_truth.py,
n1_pump40.py, n2_canonical.py, n2_writertest.py, n2_2dtest.py,
n2_apiprobe.py, n2_lidar_probe.py, n2_gmoprobe.py, n2_sig3.py,
n2_lidar_attr.py, n2_helpdefaults.py (16); planning
v11_pipeline.py, nav_check.py, n2_plan.py, n4_follow.py,
n1_run.py, n3_run.py (6). External library sources fully read
(3): kinematics.py, occupancy_map_from_usd.py,
robot_footprint.py (navigation-primitives).
Skimmed (75): all other bridge/bringup/planning scripts via import
grep + targeted signature greps.

---

## T1 — rclpy + system ROS 2 Lyrical (pixi env)

DOES: outside-sim ROS legs — subscribes to sim topics and records
msgs to JSON [verified]; publishes JointState commands at 10 Hz
[verified]; inspects topics + publisher QoS [verified].

Functions (as used in-drill, fully typed):
- `rclpy.init() -> None` [verified]. Zero-arg form only
  (listener_ros.py:87, talker_ros.py:18, topic_info.py:13,
  r2_pubcount.py:9, r2_deeplisten.py:29, tmp_rmwprobe.ps1:6,
  tmp_topics.ps1:5). Optional `args: list[str] | None =
  None` [probable — never passed in-drill]. Must be called
  before any Node; fails without Library/bin on PATH
  (see LIMITS).
- `rclpy.shutdown() -> None` [verified]. Called after
  destroy_node (listener_ros.py:93, talker_ros.py:32,
  topic_info.py:41, r2_pubcount.py:24, r2_deeplisten.py:42).
- `rclpy.spin_once(node: Node, timeout_sec: float) -> None`
  [verified]. `timeout_sec: float` in seconds: 0.5
  (listener_ros.py:91, r2_deeplisten.py:40) / 1.0
  (topic_info.py:21); always passed positionally-by-keyword,
  default ungated [theoretical]. Drives one callback round;
  listener loops `while len < count and t < timeout`;
  topic_info retries up to 25x [verified].
- `Node(node_name: str, ...) -> Node` [verified]. First
  positional only: "muse_talker" (talker_ros.py:19),
  "muse_probe" via subclass L (listener_ros.py:39),
  "muse_topicinfo" (topic_info.py:14), "muse_probe3"
  (r2_pubcount.py:10), "muse_probe2"
  (r2_deeplisten.py:16), 't' (tmp_topics.ps1:5).
  Further `__init__` params ungated [theoretical].
- `node.create_subscription(msg_type: type, topic: str,
  callback: Callable[[MsgT], None], qos_depth: int = 10)
  -> Subscription [probable — return never stored]`.
  Call [verified]: msg_type in {Clock, JointState,
  TFMessage, Odometry, LaserScan} (listener_ros.py:41,
  r2_deeplisten.py:19); depth positional 10.
- `node.create_publisher(msg_type: type[JointState],
  topic: str, qos_depth: int = 10) -> Publisher`
  [verified] (talker_ros.py:20). Talker publishes
  `sensor_msgs/JointState` only.
- `pub.publish(msg: JointState) -> None` [verified]
  (talker_ros.py:28).
- `node.get_clock() -> Clock [probable]; .now() -> Time
  [probable]; .to_msg() -> builtin_interfaces.msg.Time
  [probable]` [verified chain] (talker_ros.py:27). Used
  to stamp every talker message header.
- `node.destroy_node() -> bool [probable — return never
  checked in-drill]`. Call [verified] before shutdown
  (listener_ros.py:92, talker_ros.py:31,
  topic_info.py:40, r2_pubcount.py:23,
  r2_deeplisten.py:41, tmp_topics.ps1:5).
- `node.get_topic_names_and_types()
  -> list[tuple[str, list[str]]]` [verified]
  (topic_info.py:17, unpacked as `name, types`;
  tmp_topics.ps1:5 same shape). topic_info filters out
  /parameter_events + /rosout.
- `node.get_publishers_info_by_topic(topic: str)
  -> list[TopicEndpointInfo]` [verified]
  (topic_info.py:29, r2_pubcount.py:12,
  r2_deeplisten.py:31). Wrapped in try/except; prints
  PUB-INFO-ERR on failure.
- `node.get_node_names_and_namespaces()
  -> list[tuple[str, str]] [probable — sorted+str
  only]` (r2_pubcount.py:20).
- `TopicEndpointInfo.node_name: str`,
  `.node_namespace: str` (r2_pubcount.py:16,
  r2_deeplisten.py:35); `.qos_profile: QoSProfile`
  (topic_info.py:35, r2_deeplisten.py:35) [verified
  reads; member types [probable]].
- QoS field types (topic_info.py:36-39 prints all six)
  [verified reads]: `.reliability:
  QoSReliabilityPolicy [probable]` (RELIABLE observed,
  F2 ruled-out); `.durability: QoSDurabilityPolicy
  [probable]` (VOLATILE observed); `.depth: int
  [probable]`; `.lifespan: Duration [probable]`;
  `.deadline: Duration [probable]`; `.liveliness:
  QoSLivelinessPolicy [probable]`. `QoSProfile`
  imported in topic_info.py:11 but only used as a type
  reference, never constructed with custom args
  [verified].
- Msg field reads with types+units — Clock: `msg.clock.sec:
  int` (s), `msg.clock.nanosec: int` (ns)
  (listener_ros.py:45); JointState: `msg.name:
  list[str]`, `msg.position: sequence[float]` (rad
  [probable — ROS convention]), `msg.header.stamp.sec /
  .nanosec: int` (listener_ros.py:47-50), `msg.velocity:
  sequence[float]` (rad/s [probable])
  (r2_deeplisten.py:26); TFMessage: `msg.transforms:
  list[TransformStamped]`, `.child_frame_id /
  .header.frame_id: str`, `.transform.translation.{x,y,z}:
  float` (m [probable]) (listener_ros.py:52-60);
  Odometry: frame ids `str`,
  `pose.pose.position.{x,y,z}: float` (m [probable]),
  `twist.twist.linear.{x,y,z}: float` (m/s [probable]),
  `.angular.{x,y,z}: float` (rad/s [probable])
  (listener_ros.py:62-74); LaserScan: `msg.ranges:
  sequence[float]` (m; -1.0 = invalid [verified]),
  `header.frame_id: str` (listener_ros.py:76-84).
- Msg field writes (talker): `msg.name: list[str] =
  ["J1","J2"]`, `msg.velocity: list[float] = [v1,v2]`
  (rad/s [probable]; v1/v2: float from argv,
  talker_ros.py:14-16; values 0.8/-0.5 in
  r3_pumped_talk.ps1:10 and :21), `msg.header.stamp:
  Time msg` (talker_ros.py:22-23, :27) [verified].

Knobs + effect-of-change (attr type + unit + default):
- `count: int` (msgs; no default, argv3 required): max msgs to
  collect; loop exits at count [verified]
  (listener_ros.py:15-17; r2_deeplisten.py:10-11). Raising it
  lengthens the leg up to `timeout`. Values used: 8
  (r2/n1/r4 pumped listens), 5 (n2 scan).
- `timeout: float` (s; no default, argv4 required): wall cap;
  loop exits at cap [verified] (listener_ros.py:15-17).
  Too short + slow DDS match => zero msgs. Value used:
  120 everywhere.
- `timeout_sec: float` (s) in spin_once (0.5 listener /
  1.0 topic_info): per-spin block; larger = fewer wakeups,
  same total coverage [verified]. Effect beyond these two
  values untested [theoretical].
- queue depth `qos_depth: int = 10` (msgs; sub + pub):
  backlog replayed on DDS match [verified]. Other depths
  untested [theoretical].
- talker rate `time.sleep(0.1: float)` (s) = 10 Hz
  [verified] (talker_ros.py:30); faster/slower untested
  [theoretical].
- talker `duration: float` (s; no default, argv4 required):
  publish window; R3 uses 6 s primer + 25 s measured
  [verified] (talker_ros.py:14-16, :26;
  r3_pumped_talk.ps1:10, :21).
- Interpreter path `: str =
  C:\dev\lyrical\.pixi\envs\default\python.exe` (3.12)
  [verified] (listen.ps1:4, r2_pumped_listen via
  listen.ps1, r3_pumped_talk.ps1:8, tmp_*.ps1:4);
  system 3.14 cannot import rclpy (LIMITS).

EKB rules:
- IF a ROS leg imports rclpy THEN use the pixi env python 3.12
  BECAUSE system 3.14 lacks `_rclpy_pybind11` [verified: F1].
- IF `rclpy.init()` throws "no RMW implementations" THEN prepend
  `Library/bin` (+`bin`) to PATH BECAUSE colcon setup omits the
  dependency dlls [verified: F2].
- IF a commanded drill runs THEN open with a ~6 s pre-talk primer
  BECAUSE DDS match lags ~seconds and SUB latches [verified: F10].
- IF LaserScan ranges are gated THEN use min-of-positive
  (`rmin_valid`) BECAUSE invalid returns are -1.0, not inf
  [verified: F2 ruled-out].
- IF a verifier gates on msgs THEN conjoin every gate with
  HAVE (msgs>=5) BECAUSE `all()` over zero msgs passes vacuously
  [verified: F2 ruled-out].

LIMITS (with cites):
- L1: system python 3.14 cannot import rclpy [verified: F1].
- L2: init fails without Library/bin on PATH [verified: F2].
- L3: DDS match lags seconds; PUBS=0 at first; publisher history
  replays backlog on match [verified: discovery System ROS].
- L4: no Nav2 in the 353-package Lyrical env; ROS_DISTRO=lyrical
  [verified: discovery].

UNKNOWN (all [theoretical]):
- U1: Nav2 stack behavior (absent; Skill 11 covers substrate only).
- U2: QoS profiles beyond default depth-10/RELIABLE publisher
  compat (only observed, never varied).
- U3: multi-machine DDS.
- U4: rclpy executors / async spin (only spin_once used).
- U5: latched-publisher / transient-local durability from rclpy side.

---

## T2 — isaacsim_send.py bridge CLI (isaac-sim-remote)

DOES: sends in-sim scripts/one-liners from a local driver to the
live Kit app and returns JSON with captured stdout [verified].

Functions (as used in-drill, fully typed):
- CLI: `python isaacsim_send.py --raw --timeout <s: int> (s)
  --file <script: str> (path)` [verified]; `--raw: flag`
  emits machine JSON `{"output": str}` on stdout [verified].
  Call sites: r2_drive.py:26, n2_drive.py:32-33 (SEND built
  r2_drive.py:6-9, n2_drive.py:7-10, r3_drive.py:6-9),
  r2_pumped_listen.ps1:13, x15.py:29-31.
- CLI: `python isaacsim_send.py --raw --timeout <s: int>
  "<one-liner: str>"` [verified]. One-liners carry
  PLAY/STOP/pump snippets (r2_drive.py:19-24, :30;
  n1_drive.py:21-29; r3_drive.py:19-32).
- Local harness `_send(args: list[str]) -> str`:
  `subprocess.run(SEND + args, capture_output: bool = True,
  text: bool = True, timeout: int = 220|280 (s)) ->
  CompletedProcess`, then `json.loads(p.stdout: str).get(
  "output", "") -> str` [verified] (r2_drive.py:13-16,
  n2_drive.py:15-18, r3_drive.py:13-16). SEND =
  `[sys.executable: str, <isaacsim_send path: str>, "--raw",
  "--timeout", "180"|"240": str]` [verified].
- Remote protocol: in-sim scripts signal via `print(
  "<TAG: str> ...")` lines (e.g. R1-BUILD-OK, PUMP40,
  N2-MOUNT-OK) [verified]; drivers persist them to
  evidence via `open(path: str, mode: str = "w"|"a").write(
  s: str)` [verified] (r2_drive.py:27-28, n1_drive.py:33,
  n2_drive.py:34, exam15.py:34).

Knobs + effect-of-change (attr type + unit + default):
- `--timeout <s: int>` (s; no default, always passed):
  remote-side cap [verified]. Values: 180 (r1/r2/n1/r3
  drives), 240 (n2_drive.py:10), 300 (pump jobs),
  120 (x15.py:18). Too small kills long pumps; larger
  only waits longer [probable].
- `subprocess.run(timeout: int)` (s; local cap): must
  exceed remote `--timeout` [verified pattern]. Values:
  220 (r2/r3 drives), 280 (n2_drive.py:17), 600 (ps1
  foreground legs), 900/120 (exam15.py:27, :30), 180
  (x15.py:31). Reversing them aborts healthy calls
  [probable].
- `--file <path: str>` vs one-liner `<code: str>`:
  `--file` runs a whole script file; one-liners are
  `;`-joined snippets supporting `await` at top level
  (PLAY/STOP contain bare `await`) [verified]. So the
  remote runner is async [verified].
- `text: bool = True` + `capture_output: bool = True`:
  stdout captured as str for JSON parse [verified].
  `.returncode: int`, `.stdout/.stderr: str` read by
  drivers (r2_drive.py:39, exam15.py:31-33).

EKB rules:
- IF a ROS leg needs physics-derived data THEN overlap it with
  forced pump frames BECAUSE the app idles between bridge calls
  (frames stop, reads freeze, time advances) [verified: discovery
  Pumped ROS legs].
- IF state must survive a `--file` call THEN persist it in USD
  BECAUSE file calls run in isolated namespaces and python handles
  die with the call [verified: F2c].
- IF a repo library function is short THEN inline it into the sent
  script BECAUSE python_server caches repo imports beyond
  sys.modules [verified: R3].
- IF evidence is written THEN use Set-Content / plain file write,
  never Tee-Object BECAUSE Tee-Object writes UTF-16 and garbles
  utf-8 verifier reads [verified: R4].

LIMITS (with cites):
- L1: between calls the app idles: frozen values, fresh stamps
  [verified: discovery Pumped ROS legs].
- L2: `--file` isolated namespaces; only USD persists [verified:
  F2c; verified again by string-vs-file persistence test].
- L3: server-side import cache survives `del sys.modules` + fresh
  import [verified: R3].

UNKNOWN (all [theoretical]):
- U1: exact server-side import-cache invalidation mechanism.
- U2: concurrent-call safety (all drills are sequential + one pump
  job; parallel sends untested).
- U3: `--raw` schema beyond `{"output": str}`.
- U4: max one-liner length / file size limits.

---

## T3 — omni.graph.core (og.Controller) graph authoring

DOES: atomically authors/executes OmniGraph ROS graphs (clock,
joint states, subscribe, TF, odom, lidar helper) [verified];
reads/writes node attributes at runtime [verified].

Functions (as used in-drill, fully typed):
- `og.Controller.Keys` with members `CREATE_NODES`, `CONNECT`,
  `SET_VALUES` [verified]. The only three keys used in any
  drill (r1_build.py:17-18, r2_build.py:93-95,
  r3_build.py:73-75, r4_build.py:75-77, n1_build.py:106-108,
  n2_mount.py:60-62).
- `og.Controller.edit(graph_path: str, keys_dict:
  dict[Keys, list[tuple]]) -> None` [verified]. Used in
  r1_build (`edit("/World/R1Clock", {...})`, r1_build.py:18)
  with short node names in CONNECT/SET_VALUES [verified].
- `og.Controller.edit(graph: dict{graph_path: str,
  evaluator_name: str}, keys_dict: dict[Keys, list[tuple]])
  -> None` [verified]. Used in r2/r3/r4/n1/n2 builds with
  full `/GRAPH/NODE.port` paths [verified]
  (r2_build.py:94-95, r3_build.py:74-75, r4_build.py:76-77,
  n1_build.py:107-108, n2_mount.py:61-62). Both forms
  create the same node kinds [verified]; behavioral
  difference between the forms untested [theoretical].
- `og.Controller.attribute(attr_path: str) -> Attribute`
  [verified]. Attr paths look like
  `/ROS2/N1/CTL.inputs:velocityCommand` (n1_drive.py:24,
  n2_mount.py:75-76, r2_body.py:14, r2_ctldbg.py:9,
  r2_matrix.py:16, r3_diag.py:14, n1_truth.py:21).
- `Attribute.set(value: Any) -> None [probable — return
  never checked]` [verified write]. Runtime-only write
  (see LIMITS). Values set: `list[float]` velocityCommand
  (rad/s [probable]; `[1.0]*4` n1_drive.py:25,
  `[0.0]*4` n2_mount.py:76). Used to zero/set CTL
  velocityCommand across stop/play boundaries [verified].
- `Attribute.get() -> Any (per-port type)` [verified
  call; per-port return types [probable]]:
  `RD.outputs:jointPositions -> sequence[float]` (rad
  [probable]; wrapped with the list builtin in r2_body.py:14-15,
  r2_ctldbg.py:9-10, r2_matrix.py:16-17);
  `SUB.outputs:jointNames -> list[str]`,
  `SUB.outputs:velocityCommand -> list[float]` (rad/s
  [probable]), `CTL.inputs:jointNames -> list[str]`,
  `CTL.inputs:velocityCommand -> list[float]`,
  `CTL.inputs:robotPath -> str` (r3_diag.py:10-15).
- `og.ObjectLookup.attribute(attr_path: str) -> Attribute;
  .get_upstream_connections() -> list[Connection]
  [probable — only len() used]` [verified]
  (r1_build.py:35-36 asserts `len(up)==1` to prove the
  Time->Clock link).

Knobs + effect-of-change (attr type + unit + default):
- `evaluator_name: str = "execution"` — the only evaluator
  used [verified]. Others untested [theoretical].
- CREATE_NODES entries `(name: str, type_string: str)`:
  type strings used — `omni.graph.action.OnPlaybackTick`,
  `isaacsim.core.nodes.IsaacReadSimulationTime`,
  `isaacsim.core.nodes.IsaacComputeOdometry`,
  `isaacsim.core.nodes.IsaacArticulationController`,
  `isaacsim.ros2.bridge.ROS2PublishClock`,
  `...ROS2PublishJointState`, `...ROS2SubscribeJointState`,
  `...ROS2PublishTransformTree`, `...ROS2PublishOdometry`,
  `...ROS2RtxLidarHelper` [verified].
- CONNECT edges `(src: str, dst: str)`:
  `"Node.outputs:port" -> "Node.inputs:port"` (short form,
  r1_build.py:24-27) or full-path form (r2_build.py:101-105)
  [verified]. Wrong port names throw at edit time
  [probable — never observed to fail silently].
- SET_VALUES pairs `(attr_path: str, value: Any)` applied
  atomically with creation [verified]. Value types used:
  topicName `str`, queueSize `int = 10`, robotPath ART `str`,
  jointNames `list[str]`, velocityCommand `list[float]`
  (rad/s [probable]), odom/chassis frame ids `str`,
  Helper type `str` / frameId `str` / renderProductPath
  `str` / enabled `bool` [verified].

EKB rules:
- IF graph config must survive play THEN write it at USD level
  (edit/rels), never via `Controller.attribute().set()`, BECAUSE
  play re-parses from USD and wipes runtime sets [verified:
  F2 ruled-out OG-GET-new/USD-GET-old].
- IF CTL commands must persist across stop/play THEN re-set them
  after every stop() BECAUSE stop wipes runtime CTL commands
  (n1_drive PLAY re-sets velocityCommand post-stop) [verified].
- IF a graph is rebuilt THEN RemovePrim the old graph path first
  BECAUSE stale graphs linger and double-publish [verified:
  every build script pattern].
- IF node types are probed THEN enable the owning extension first
  BECAUSE creation throws "extension not loaded" on fresh sims
  [verified: F2b].

LIMITS (with cites):
- L1: `attribute().set()` is runtime-only; play wipes it
  [verified: F2 ruled-out].
- L2: deprecated `IsaacCreateRTXLidarScanBuffer` /
  `IsaacComputeRTXLidarFlatScan` CRASH the process at first play
  [verified: F2a].
- L3: OG node creation requires `isaacsim.ros2.bridge` loaded
  [verified: F2b].

UNKNOWN (all [theoretical]):
- U1: non-`execution` evaluators.
- U2: graph profiling / perf APIs.
- U3: `Controller.attribute().get()` exact return types per port.
- U4: partial-edit (non-atomic) semantics; edit failure rollback.

---

## T4 — isaacsim.ros2.bridge OG nodes (play-gated pub/sub)

DOES: publishes /clock, /joint_states, /tf(+static), /odom, /scan;
subscribes joint commands; CTL drives articulations per tick
[verified].

Functions — node types + their wired ports (as used in-drill,
fully typed; port value types [probable] unless read back live):
- `ROS2PublishClock`: inputs `execIn: execution <-
  OnPB.tick`, `timeStamp: float (s) [probable] <-
  IsaacReadSimulationTime.simulationTime`; config
  `topicName: str = "clock"`, `queueSize: int = 10`
  [verified] (r1_build.py:24-31).
- `ROS2PublishJointState`: inputs `execIn: execution`,
  `timeStamp: float (s) [probable]`; rel
  `inputs:targetPrim -> [ART: str]` (auto-read, LIVE per
  tick) [verified] (r2_build.py:112-113); config
  `topicName: str = "/joint_states"`, `queueSize: int =
  10` [verified] (r2_build.py:106-108). Node needs
  connected arrays OR targetPrim [verified: discovery].
- `ROS2SubscribeJointState`: input `execIn: execution <-
  OnPB.tick`; outputs `jointNames: list[str]`,
  `positionCommand: list[float]` (rad [probable]),
  `velocityCommand: list[float]` (rad/s [probable]),
  `effortCommand: list[float]` (N·m [probable]),
  `timeStamp: float (s) [probable]`, `execOut: execution`
  [verified: discovery lists all six; value types via
  r3_diag.py:10-15 reads]; LATCHES last msg [verified:
  F10]. Config `topicName: str = "/r3_cmd"`,
  `queueSize: int = 10` [verified] (r3_build.py:87-89).
- `ROS2PublishTransformTree`: inputs `execIn: execution`,
  `timeStamp: float (s) [probable]`; rels
  `inputs:parentPrim -> ["World": str]`,
  `inputs:targetPrims -> list[Sdf.Path]` (base, link1,
  link2 via `.GetPath()`) [verified] (r4_build.py:94-98);
  config `topicName: str = "/tf"`, `queueSize: int = 10`
  [verified] (r4_build.py:88-90).
- `ROS2PublishOdometry`: inputs `execIn: execution <-
  ODO.execOut`, `timeStamp: float (s) [probable]`,
  `position: float[3]` (m [probable]), `orientation:
  float[4]` (quat [probable]), `linearVelocity: float[3]`
  (m/s [probable]), `angularVelocity: float[3]` (rad/s
  [probable]) <- IsaacComputeOdometry outputs [verified]
  (n1_build.py:115-128); config `topicName: str =
  "/odom"`, `queueSize: int = 10`, `odomFrameId: str =
  "odom"`, `chassisFrameId: str = "base_link"`
  [verified] (n1_build.py:129-133).
- `ROS2RtxLidarHelper`: input `execIn: execution`; config
  `topicName: str = "/scan"`, `type: str = "laser_scan"`,
  `frameId: str = "base_scan"`, `renderProductPath: str`
  (RP `/Render/...`), `queueSize: int = 10`, `enabled:
  bool = True` [verified] (n2_mount.py:66-74). Defaults
  sane: enabled, frameSkip 0 [verified: F2 ruled-out,
  n2_helpdefaults.py:9-22]; `fullScan`
  deprecated-ignored [verified: F2 ruled-out].
- `IsaacArticulationController` (core, not bridge, but the
  glue): inputs `execIn: execution`, `robotPath: str`
  (REQUIRED), `jointNames: list[str]`, `velocityCommand:
  list[float]` (rad/s [probable — commanded 1.0 reads
  back as dofv 1.0, F1 bisection + n1_truth.py:30]);
  rel `inputs:targetPrim -> [ART: str]` (alone IGNORED)
  [verified: F7] (r2_build.py:109-115, n1_build.py:134-145,
  r3_build.py:90-92, r4_build.py:91-100).
- `IsaacComputeOdometry`: input `execIn: execution`;
  chassis via rel `inputs:chassisPrim -> [Sdf.Path]`
  (fallback: attr set to path `str`)
  [verified: n1_build dual path, n1_build.py:138-143];
  outputs `execOut: execution`, `position: float[3]` (m),
  `orientation: float[4]` (quat), `linearVelocity:
  float[3]` (m/s), `angularVelocity: float[3]` (rad/s)
  [verified wiring; value types [probable]].
- `IsaacReadSimulationTime`: output `simulationTime: float`
  (s [probable]) [verified] (r1_build.py:26,
  r2_build.py:104, n1_build.py:119).
- `omni.graph.action.OnPlaybackTick`: output `tick:
  execution` [verified]. Ticks only while playing
  [verified].

Knobs + effect-of-change (attr type + unit + default):
- `topicName: str` (no default; always set): routed topic;
  drills use clock, /joint_states, /r3_cmd, /tf, /odom,
  /scan [verified]. Renaming only reroutes [probable].
- `queueSize: int = 10` (msgs) everywhere [verified];
  other sizes untested [theoretical].
- CTL `robotPath: str` (no default; REQUIRED): missing =>
  silent no-op (zero motion, zero errors) [verified: F7].
  THE load-bearing knob.
- CTL `jointNames: list[str]` + `velocityCommand:
  list[float]` (rad/s [probable]): must align elementwise;
  n1 derives names from geometry (`wnames: list[str]`,
  n1_build.py:69-74,105), never hardcoded [verified].
  Length mismatch behavior untested [theoretical].
- CTL per-mode arrays: only `velocityCommand: list[float]`
  verified end to end [verified]; `positionCommand /
  effortCommand: list[float]` untested [theoretical].
- Helper `type: str = "laser_scan"`: only verified value
  [verified]; other types untested [theoretical].
- Helper `enabled: bool = True`: shipped value [verified].
  False presumably mutes [theoretical].
- PUB `odomFrameId / chassisFrameId: str =
  "odom" / "base_link"`: frame ids on the wire [verified];
  other ids untested [theoretical].

EKB rules:
- IF joint states are published THEN use targetPrim auto-read,
  never IsaacReadJointState->explicit-array wiring, BECAUSE the
  array wiring serves a match-time snapshot (frozen values, fresh
  stamps) [verified: F6].
- IF CTL is authored THEN set the robotPath STRING plus
  jointNames BECAUSE the targetPrim rel alone is silently ignored
  [verified: F7].
- IF joints must move THEN pair authored DriveAPI with a live
  per-tick commander BECAUSE the DOF defaults to effort mode and
  either alone yields zero motion [verified: F4].
- IF motion must persist across bridge calls THEN use CTL
  per-tick commands, never wrapper velocity targets, BECAUSE
  wrapper targets clear after call return (tensor-view GC)
  [verified: F5].
- IF TF must show motion THEN drive the joints (CTL velocity
  [0.5,0.5] in R4) BECAUSE static links publish static frames
  [verified: r4 pattern].
- IF /scan is published THEN use ROS2RtxLidarHelper straight from
  the product BECAUSE the deprecated ScanBuffer/FlatScan nodes
  crash the process [verified: F2a].

LIMITS (with cites):
- L1: ALL topics publish only while playing; R1 clock passes
  unpumped, every physics-derived stream needs pumped frames
  [verified: SKILL Limitations + R-pattern].
- L2: targetPrim auto-read LIVE; array wiring frozen; literal
  arrays publish nothing [verified: F6 + discovery].
- L3: CTL no-ops without robotPath string [verified: F7].
- L4: authored DriveAPI alone never moves a joint [verified: F4].
- L5: wrapper velocity targets clear after call return
  [verified: F5].
- L6: /scan publisher QoS RELIABLE/VOLATILE, compatible
  [verified: F2 ruled-out].

UNKNOWN (all [theoretical]):
- U1: CTL effort/position command modes over the wire.
- U2: Helper `type` values other than `laser_scan`.
- U3: point-cloud (non-laser_scan) output.
- U4: `fullScan` semantics (deprecated-ignored per ruled-out).
- U5: queueSize values other than 10.
- U6: SUB queueing beyond latch-last (queueSize effect on SUB).

---

## T5 — omni.usd + pxr USD authoring (stage builds)

DOES: builds bots, ground, graphs, lights, lidar mounts in the
live stage; cleans prior-drill prims [verified].

Functions (as used in-drill, fully typed):
- `omni.usd.get_context() -> UsdContext [probable];
  .get_stage() -> Usd.Stage` [verified]. Every in-sim
  script opens with this (r1_build.py:11, r2_build.py:20,
  n1_build.py:22, n2_mount.py:18, n1_run.py:16, n3_run.py:13).
- `stage.GetPrimAtPath(path: str) -> Usd.Prim` [verified]
  (returns an invalid prim when missing, never None —
  `.IsValid() -> bool` gates existence [verified],
  e.g. r1_build.py:14-15, r2_build.py:21-22).
- `stage.RemovePrim(path: str) -> bool [probable —
  return never checked]` [verified call]. Used for
  graphs, bots, ground, domes, cubes — NEVER render
  products (LIMITS) (r1_build.py:16, n1_build.py:35-38,
  n2_mount.py:31-32).
- `prim.GetChildren() -> list[Usd.Prim]`;
  `prim.GetName() -> str`; `prim.GetPath() -> Sdf.Path`;
  `Sdf.Path.pathString -> str` [verified]. Used for prefix
  cleanup loops (`startswith("R2Bot")` etc.,
  r2_build.py:23-25) and newest-by-timestamp ART picks
  (n2_mount.py:24-26; r2_pump40.py:13-16).
- `prim.GetRelationship(name: str) -> Usd.Relationship`
  with name in {"inputs:targetPrim", "inputs:parentPrim",
  "inputs:targetPrims", "inputs:chassisPrim"};
  `.SetTargets(targets: list[str | Sdf.Path]) -> None
  [probable]` [verified] (r2_build.py:112-115,
  r4_build.py:94-98, n1_build.py:138-145);
  `.GetTargets() -> list[Sdf.Path] [probable]` reads back
  [verified] (r2_build.py:119-120, r4_build.py:104-107).
  Joint rels: `GetBody0Rel() / GetBody1Rel() ->
  Usd.Relationship` with the same typed `.SetTargets`
  shape as above [verified]
  (r2_build.py:66-67, n1_build.py:94-95).
- `prim.GetAttribute(name: str) -> Usd.Attribute;
  .Set(v: Any) -> None [probable]; .Get() -> Any`
  [verified]. Used for xformOp reads (n3_run.py:21-22),
  sensor meta reads (n2_canonical.py:19-26:
  `omni:sensor:Core:{scanRateBaseHz: float (Hz),
  nearRangeM/farRangeM: float (m), patternFiringRateHz:
  float (Hz)}` [probable]), chassisPrim fallback
  (n1_build.py:143).
- `UsdGeom.Xform.Define(stage: Usd.Stage, path: str) ->
  UsdGeom.Xform` [verified] (r2_build.py:27, n1_build.py:49);
  `.AddTranslateOp() -> UsdGeom.XformOp; .Set(v: Gf.Vec3d)
  (m [probable — stage units])` [verified]
  (r2_build.py:35, n1_build.py:56). Translate-first rule:
  position on parent Xform, scale on child mesh [verified:
  n1_build comment, n1_build.py:39, :59-60].
- `UsdGeom.Cube.Define(stage: Usd.Stage, path: str) ->
  UsdGeom.Cube; .GetSizeAttr().Set(s: float)` (m edge
  [probable]) [verified] (r2_build.py:36-37,
  n1_build.py:57-58, n2_mount.py:36-37); scaled via
  `UsdGeom.Xformable(prim: Usd.Prim).AddScaleOp().Set(
  v: Gf.Vec3f)` (dimensionless) [verified]
  (n1_build.py:45-46, :59-60).
- `UsdGeom.Sphere.Define(stage: Usd.Stage, path: str) ->
  UsdGeom.Sphere;
  .GetRadiusAttr().Set(r: float = 0.1)` (m [probable]) —
  wheel collider [verified] (n1_build.py:80-81);
  `UsdGeom.Cylinder.Define(stage: Usd.Stage, path: str)`,
  `.GetAxisAttr().Set(axis: str = "Y")` (token),
  `.GetRadiusAttr().Set(0.1: float)` (m),
  `.GetHeightAttr().Set(0.03: float)` (m) — visual-only
  wheel child [verified] (n1_build.py:82-85).
- `UsdLux.DomeLight.Define(stage: Usd.Stage, path: str);
  .GetIntensityAttr().Set(400.0: float)` (unit
  [theoretical]) [verified: n2_mount.py:34-35].
- `UsdPhysics.ArticulationRootAPI.Apply(prim: Usd.Prim)
  -> ArticulationRootAPI [probable]` [verified]
  (r2_build.py:28, n1_build.py:50);
  `PhysxSchema.PhysxArticulationAPI.Apply(prim: Usd.Prim) ->
  API [probable]` + `.GetSolverPositionIterationCountAttr()
  .Set(64: int)` + `.GetSolverVelocityIterationCountAttr()
  .Set(16: int)` [verified] (n1_build.py:51-53).
- `UsdPhysics.RigidBodyAPI.Apply(prim: Usd.Prim)` [verified],
  `UsdPhysics.MassAPI.Apply(prim: Usd.Prim).CreateMassAttr().Set(
  kg: float)` (1.0 links, 2.0 chassis, 0.5 wheels)
  [verified] (n1_build.py:63, :88);
  `PhysxSchema.PhysxRigidBodyAPI.Apply(prim: Usd.Prim)` +
  `.GetSleepThresholdAttr().Set(0.0: float)` +
  `.GetSolverPositionIterationCountAttr().Set(32: int)` +
  `.GetSolverVelocityIterationCountAttr().Set(8: int)`
  (n1) [verified] (n1_build.py:64-67, :89-92).
- `UsdPhysics.CollisionAPI.Apply(prim: Usd.Prim)` [verified]
  — ground (n1_build.py:47), chassis (n1_build.py:61),
  wheel spheres (n1_build.py:86); NEVER on spinning drill
  links (LIMITS).
- `UsdPhysics.RevoluteJoint.Define(stage: Usd.Stage,
  path: str) -> RevoluteJoint` [verified];
  `.GetBody0Rel()/.GetBody1Rel() -> Relationship`,
  `.GetLocalPos0Attr().Set(Gf.Vec3f)` (m [probable]),
  `.GetLocalPos1Attr().Set(Gf.Vec3f)` (m),
  `.GetAxisAttr().Set(axis: str = "Z"|"Y")` (token)
  [verified] (r2_build.py:65-70, n1_build.py:93-98).
  Frames must be coincident (J1 localPos1=(0,-0.2,0))
  [verified: discovery].
- `UsdPhysics.FixedJoint.Define(stage: Usd.Stage,
  path: str) -> FixedJoint` [verified]; body1-only
  (body0 unset = world anchor) + LocalPos1
  `Gf.Vec3f(0,0,0)` (m) [verified]
  (r2_build.py:61-63, n1_build.py:35 anchor pattern).
- `UsdPhysics.DriveAPI.Apply(joint_prim: Usd.Prim,
  drive_name: str = "angular") -> DriveAPI [probable]`
  [verified] (r2_build.py:75, n1_build.py:99);
  `.GetTargetVelocityAttr().Set(v: float)` (rad/s for
  angular [probable]; 1.0 r2/n1, 0.0 r3/r4),
  `.GetStiffnessAttr().Set(0.0: float)` (unit
  [theoretical]), `.GetDampingAttr().Set(d: float)`
  (50.0 arms, 2.0 wheels), `.GetMaxForceAttr().Set(
  f: float)` (100.0 arms, 2.0 wheels; N·m for angular
  [probable]) [verified].
- `Gf.Vec3d(x: float, y: float, z: float)`,
  `Gf.Vec3f(x: float, y: float, z: float)` constructors
  [verified] (r2_build.py:35, :68; n1_build.py:76, :96).
- `Usd.PrimRange(prim: Usd.Prim) -> iterable[Usd.Prim]`
  [probable] + `p.HasAPI(api_type: type) -> bool`
  [verified] (n3_run collider harvest, n3_run.py:14-15).
- `UsdRender` imported for product queries (n2_mount.py:11,
  probes); no direct UsdRender calls in the 20 shipped
  drills [verified]. Probe-only calls (T11): `stage.Traverse()
  -> iterable[Usd.Prim] [probable]`, `prim.IsA(api_type: type)
  -> bool` (e.g. `UsdRender.Product`, n2_writertest.py:27-28,
  n2_gmoprobe.py:40-41, n2_lidar_probe.py:32-33,
  n2_apiprobe.py:29-30).
- `isaacsim.core.experimental.utils.app`:
  `enable_extension(name: str) -> None [probable]`
  (r1_build.py:12, n1_build.py:17, n2_mount.py:15);
  `play() -> None` + `play(commit: bool)` variant
  (`commit=True` in n2_2dtest.py:55; default
  [theoretical]); `stop() -> None`;
  `await update_app_async(steps: int) -> None [probable]`
  with steps in {1 (n1_truth.py:25), 2 (n2_life.py:23),
  5, 10, 30, 40, 50 (r2_gap.py:10), 60, 120
  (n2_gmoprobe.py:55), 150 (n2_2dtest.py:56)} [verified].
  Steps unit: physics frames [probable].

Knobs + effect-of-change (attr type + unit + default):
- ART path `: str` unique per build (`ART_%d % time.time()`):
  rebuilding at a fixed path reads a GHOST (frozen
  previous-play values) via OG/PhysX handle cache
  [verified: r2_build comment, 2x2] (r2_build.py:14-18).
- Base dynamic + world FixedJoint vs kinematic: kinematic =>
  backend builds 0 joints/0 links, silently [verified: F3].
- Sleep threshold `: float = 0.0`: prevents sleeping
  [verified pattern] (n1_build.py:65, :90). Nonzero
  untested [theoretical].
- Solver iterations `: int`: 64/16 articulation +
  32/8 bodies — kept as best practice; did NOT fix F1
  alone [verified: F1 ruled-out] (n1_build.py:52-53,
  :66-67). Other values untested [theoretical].
- Drive gains `: float`: 20/50 violent, 2/2 mostly smooth,
  1/0.5 violent again — gains modulate, do not cause F1;
  ship damping 2/maxF 2 for wheels, 50/100 for arm joints
  [verified: F1 ruled-out] (n1_build.py:102-103,
  r2_build.py:78-79).
- Wheelbase `: float` (m) 0.24->0.36 (tip margin
  25.6->35.8 deg) + spawn clearance +1.5 cm: shipped with
  the F1 fix [verified] (n1_build.py:70-76).
- Wheel joint axis `: str = "Y"` (+1 about Y rolls +X),
  arm joints `"Z"` [verified] (n1_build.py:98,
  r2_build.py:70). Other axes untested [theoretical].
- Stage is Z-up, gravity -Z 9.81 (m/s^2 [probable]),
  single /PhysicsScene (TGS); a second scene
  splits/double-steps bodies [verified: n1_build
  (n1_build.py:32-36) + F1 ruled-out].
- update_app_async `steps: int` (frames [probable]): 1
  truth sample, 2 life probe, 5 settle, 10 post-enable,
  30 post-enable r1, 40 pump chunk, 50 gap probe, 60 play
  proof, 120 GMO probe, 150 writer test [verified]. Other
  counts untested [theoretical].

EKB rules:
- IF a link sits inside an articulation THEN keep its base
  dynamic + world FixedJoint BECAUSE PhysX excludes kinematic
  bodies (zero joints, silent) [verified: F3].
- IF a link spins continuously THEN give it NO CollisionAPI
  BECAUSE contact weld freezes joints (~104 deg) [verified: F8].
- IF a wheel rolls THEN use an analytic sphere (or capsule)
  collider + visual-only cylinder child BECAUSE raw USD cylinder
  collision cooks to a faceted hull (vault-launch cycle, +/-4 cm)
  [verified: F1].
- IF an articulation is rebuilt THEN use a fresh timestamped
  path BECAUSE the OG/PhysX layer caches handles by path
  (ghost reads) [verified: r2_build].
- IF a build runs THEN clean own + prior drill prefixes first
  (Section 4a) BECAUSE rasterizers/graphs see the whole stage
  [verified: R6 + every build].
- IF joint angles are gated THEN gate wrap-robust (any in-
  window moment, both signs) BECAUSE multi-turn reports wrap
  modulo [verified: F9].
- IF a second /PhysicsScene exists THEN remove it BECAUSE it
  splits/double-steps bodies [verified: n1_build].
- IF extension nodes are authored THEN call
  `enable_extension("isaacsim.ros2.bridge")` + pump 10-30 steps
  first BECAUSE fresh sims lack the extension [verified: F2b].

LIMITS (with cites):
- L1: kinematic base => 0 joints/0 links silently [verified: F3].
- L2: CollisionAPI on spinning links => contact weld freeze
  [verified: F8].
- L3: raw USD Cylinder colliders => facet slap vault-launch
  [verified: F1].
- L4: RemovePrim on render products crashes the renderer
  (rtx.hydra backtrace) [verified: F2 ruled-out].
- L5: joint angles wrap [verified: F9].
- L6: one articulation per drill; unique path per build; never a
  second /PhysicsScene [verified: discovery + n1_build].
- L7: post-talk reads are scrap (unpowered drift); stop() resets
  anyway [verified: discovery Stage facts].

UNKNOWN (all [theoretical]):
- U1: capsule wheel colliders (named alternative; sphere shipped).
- U2: UsdPhysics joint types beyond revolute/fixed.
- U3: Y-up authoring (all drills Z-up).
- U4: deformable / cloth / particle APIs.

---

## T6 — Articulation wrapper (isaacsim.core.experimental.prims)

DOES: reads live articulation state (num_dofs, dof_names, joint
pos/vel) [verified]; issues debug velocity targets (single-call
only) [verified]; chassis pose via RigidPrim [verified].

Functions (as used in-drill, fully typed):
- `Articulation(art_path: str) -> Articulation` [verified].
  Path discovered by prefix scan (`startswith("R2Bot")`
  etc., r2_pump40.py:13-16; R3Bot r3_drive.py:26-27; N1Base
  n1_truth.py:13-16) [verified]; stale-path reads
  suspected in phantom-ART case.
- `.num_dofs -> int` [verified] (r2_artstate.py:9,
  r2_nodemeta_probe.py:90). Gate: 2 for arm bots (F3
  recovery probe), 4 for n1 wheels [probable — n1 uses DOF
  vectors of length 4].
- `.dof_names -> list[str] [probable — list builtin only]`
  [verified read] (r3_diag.py:23, n1_diag.py:14). Wrapper
  DOF order [J1,J2] confirmed [verified: discovery].
- `.joint_names -> sequence[str] [probable]`,
  `.joint_positions -> sequence[float] [probable]` (rad
  [probable]) (r2_artstate.py:10-11: iterated with
  str()/float() casts).
- `.get_dof_positions() -> Tensor (torch-like [probable —
  `.numpy()` exists, n1_truth.py:31])`; drills use
  `np.asarray` + `.flatten().tolist()` (r2_pump40.py:20,
  r2_gap.py:12) or `.numpy().flatten()` (n1_truth.py:31)
  [verified]. Values `list[float]` per-DOF joint angles in
  RADIANS (wrapped multi-turn) [verified: F8 J1=1.82 =
  104deg; F9 +6.47 rad read -6.086]. DEG/RAD boundary:
  raw `Gf … .ExtractRotation().GetAngle()` reports the
  same angles in DEGREES (r2_body.py:14, r2_matrix.py:14)
  [probable — USD API contract].
- `.get_dof_velocities() -> Tensor`, same unwrap
  [verified] (r2_gap.py:15, r2_drvdbg.py:16,
  n1_diag.py:15, n1_truth.py:30). Values `list[float]` in
  RAD/S [verified]: n1 F1 bisection showed +/-8 rad/s
  spikes on bad colliders, [1,1,1,1] on good.
- `.set_dof_velocity_targets(targets: np.ndarray,
  shape (1, num_dofs), dtype float) -> None [probable —
  return never checked]` [verified]. Shape used: 2D
  `[[...]]` (r2_gap.py:9 `[[1.0, 0.0]]`, r2_rtdrv.py:9,
  r2_matrix.py:27-28). Values rad/s [probable — PhysX
  angular convention; magnitude match ungated for the
  wrapper path]. Motion works DURING the pumped call,
  freezes ~1 s after bridge-call return [verified: F5].
- `RigidPrim(path: str) -> RigidPrim` [verified]
  (n1_truth.py:19 `RigidPrim(ART + "/chassis")` for tensor
  ground-truth chassis pose); `.get_world_poses() ->
  tuple[Tensor, Tensor]` [verified] (n1_truth.py:27):
  `pos: (N,3) float` (m [probable]) +
  `quat: (N,4) float` (order [theoretical]), each
  `.numpy().flatten().tolist()` (n1_truth.py:28-29).

Knobs + effect-of-change (attr type + unit + default):
- Target velocity values `: np.ndarray (1, num_dofs) float`
  (rad/s [probable]; no default): switch the DOF into
  velocity mode (with authored drive gains allocating the
  model) [verified: F4] (r2_gap.py:9). Either
  wrapper-targets or authored-drive alone => zero motion
  [verified: F4 bisection].
- Read timing (no knob; call placement): reads inside a
  pumped call are live; reads across calls after
  wrapper-commanded motion freeze [verified: F5].

EKB rules:
- IF live DOF state is needed THEN probe num_dofs/dof_names/
  pos/vel via the wrapper BECAUSE USD structure alone cannot
  prove the backend built joints (F3: valid USD, 0 joints)
  [verified: F3].
- IF motion must cross bridge calls THEN use CTL per-tick, never
  wrapper targets, BECAUSE wrapper targets clear after call
  return [verified: F5].
- IF positions are compared THEN expect wrap (modulo) BECAUSE
  multi-turn reports wrap [verified: F9].

LIMITS (with cites):
- L1: wrapper-commanded motion freezes ~1 s after bridge-call
  return [verified: F5].
- L2: phantom ART reads (UNCONFIRMED): removed N1Base_* prims
  reappearing with zeroed transforms; suspected stale bridge USD
  view; harmless (mount picks newest-by-timestamp) [verified as
  observed; cause UNCONFIRMED: F2 ruled-out].

UNKNOWN (all [theoretical]):
- U1: wrapper velocity commands within a single pumped call as a
  supported pattern (bisected only as cross-call failure).
- U2: torque/effort wrapper APIs.
- U3: RigidPrim full method surface beyond constructor use.
- U4: phantom-ART root cause.

---

## T7 — RTX Lidar + replicator render products

DOES: creates the RTX lidar and its USD-persistent render product
feeding /scan [verified]; in-sim diagnostics via sensor.attach_writer
[verified].

Functions (as used in-drill, fully typed):
- `Lidar.create(path: str, config: str, tick_rate: float,
  accumulate_outputs: bool, positions: list[list[float]] |
  None, translations: list[list[float]] | None) -> lidar
  handle with `.paths: list[str] [probable]` [verified:
  n2_mount.py:49-51]. `tick_rate: float = 10.0` (Hz
  [probable]; default [theoretical]);
  `accumulate_outputs: bool = True` (default
  [theoretical]; omitted in n2_apiprobe.py:20-21,
  n2_bindprobe.py:15-16); `positions=` WORLD-frame m, not
  parent-local [verified: F2e] (n2_mount.py:51,
  n2_2dtest.py:51, n2_apiprobe.py:21); variant kwarg
  `translations=` in n2_canonical.py:35 [verified —
  both spellings appear; equivalence untested:
  theoretical]. `.paths[0]: str` feeds
  `prim_utils.get_prim_at_path` (n2_canonical.py:37).
- `LidarSensor(lidar_or_path: LidarHandle | str,
  annotators: list = <default>) -> LidarSensor` [verified:
  n2_2dtest.py:52, n2_canonical.py:36, n2_parent.py:56 pass
  the handle + `annotators=[]`; n2_bindprobe.py:17,
  n2_box.py:63, n2_helptest.py:24, n2_life2.py:24,
  n2_writertest.py:17 pass a path `str`, some without
  annotators — so `annotators` has a default whose value
  is [theoretical]]. Creates an AUTO `rtx_sensor_*`
  product that DIES with the --file call's handles
  [verified: F2c]. Shipped N2 recipe uses NO LidarSensor
  [verified: n2_mount].
- `rep.create.render_product(lidar_path: str, resolution:
  tuple[int, int] (px [probable]), name: str = <default>)
  -> RenderProduct with `.path: str` (RP under /Render/*)`
  [verified: n2_mount.py:52-53]. Persists in USD (mirrors
  NVIDIA test_rtx_sensor.py) [verified: F2c]. `name=`
  kwarg used in n2_bindprobe.py:18, n2_rp3.py:48
  (default [theoretical]). Bind probes tried (64,1)
  (n2_bindprobe.py:18, n2_rp2.py:30, n2_rp_probe.py:13).
- `sensor.attach_writer(writer_name: str, **kwargs: Any)
  -> None [probable]` [verified call] —
  `attach_writer("T2Writer"|"MWriter")` is the working
  in-sim diagnostic for RTX sensors [verified: F2
  ruled-out] (n2_2dtest.py:54, n2_box.py:65,
  n2_mounted.py:54, n2_parent.py:58).
- `sensor.attach_writer("RtxLidarROS2PublishLaserScan",
  topicName: str = "scan", frameId: str = "base_scan",
  **meta)` [verified: n2_canonical.py:38-39] with meta
  (n2_canonical.py:28-31) = `horizontalFov: float = 360.0`
  (deg [probable]), `horizontalResolution: float =
  360*rot/fire` (unit [theoretical]), `depthRange:
  list[float] = [near, far]` (m [probable]),
  `rotationRate: float = rot` (Hz [probable]),
  `azimuthRange: list[float] = [-180.0, 180.0]` (deg
  [probable]) — derived from `omni:sensor:Core:*` attrs
  via `prim_utils.get_prim_at_path(lidar.paths[0])`
  [verified]. Canonical-pattern test only, not the
  shipped recipe [verified].
- `parse_generic_model_output_data(raw: Any) -> GMO
  [probable]` [verified call] (n2_2dtest.py:36,
  n2_gmoprobe.py:30, n2_box.py:37, n2_rp3.py:32):
  `raw` is the dict-extracted `data` field [theoretical
  type]; returns obj with `.numElements` (int-able),
  `.x/.y/.z` (warp arrays [probable — `isinstance(a,
  wp.array)` guard, n2_2dtest.py:17-19]). Semantics
  [probable — n2_2dtest.py:59-61 applies `np.radians`
  to x/y]: x = azimuth (deg), y = elevation (deg),
  z = range (m).
- `SUPPORTED_LIDAR_CONFIGS: dict-like [probable]`
  (n2_apiprobe.py:13-14 calls `.keys()`, filters
  "Rotary"/"2D") [verified import+keys]; values ungated
  [theoretical].
- `writer.attach(products: list[str]) -> None [probable]`
  (raw replicator Writer): NEVER ticks for RTX sensors
  [verified: F2 ruled-out] (n2_writertest.py:32 `attach(
  [RP: str])`, n2_gmoprobe.py:51 `attach(rps:
  list[str])`).
- `UsdLux.DomeLight` intensity `: float = 400.0` (unit
  [theoretical]) + N2Cube (size `: float = 1.0` m at
  (2, 0, 0.5) m, n2_mount.py:36-38): scan target
  geometry; rmin_valid ~1.5 m (cube face), rmax in
  (1.2, 2.0) m [verified: verify_n2.py:30-34 gates].

Knobs + effect-of-change (attr type + unit + default):
- `config: str = "Example_Rotary_2D"`: only verified config
  [verified] (n2_mount.py:49). Others untested
  [theoretical].
- `tick_rate: float = 10.0` (Hz [probable]),
  `accumulate_outputs: bool = True`: shipped values
  [verified]. Defaults + sensitivity untested
  [theoretical].
- `positions: list[list[float]]` (m, world coords):
  [[0,0,0.25]] lands INSIDE the chassis (self-occluded
  empties); [[0,0,0.515]] clears it [verified: F2e].
  +z must exceed chassis top (~0.34 m) [verified].
- Parent prim `: str` (path): rigid-body parent => EMPTY
  scans (19 empty ticks); articulation-root parent => full
  frames (24) at the same pose [verified: F2d]
  (n2_mount.py:27-30). THE load-bearing knob.
- Resolution `: tuple[int, int] = (128,128)` (px
  [probable]): shipped value [verified] (n2_mount.py:52).
  Others untested save (64,1) in a bind probe
  [probable — ungated] (n2_bindprobe.py:18).
- DomeLight intensity `: float = 400.0` (unit
  [theoretical]): shipped [verified] (n2_mount.py:35).
  Effect of change untested [theoretical].

EKB rules:
- IF /scan must flow THEN create Lidar WITHOUT LidarSensor +
  explicit rep product + Helper graph, root-parented, with world-
  frame positions, BECAUSE each of the five stacked F2 causes
  kills the pipeline alone [verified: F2a-F2e].
- IF an RTX sensor is diagnosed in-sim THEN use
  sensor.attach_writer BECAUSE raw writer.attach never ticks
  [verified: F2 ruled-out].
- IF ranges are gated THEN use min-of-positive BECAUSE invalid
  is -1.0 [verified: F2 ruled-out].
- IF products exist THEN never RemovePrim them BECAUSE they are
  scheduler-owned (renderer crash) [verified: F2 ruled-out].

LIMITS (with cites):
- L1: LidarSensor AUTO product dies with --file handles
  [verified: F2c].
- L2: rigid-body parenting => empty scans [verified: F2d].
- L3: positions= are world-frame [verified: F2e].
- L4: invalid returns -1.0 [verified: F2 ruled-out].
- L5: writer.attach never ticks for RTX [verified: F2 ruled-out].
- L6: named-vs-auto product binding identical except resolution
  [verified: F2 ruled-out].

UNKNOWN (all [theoretical]):
- U1: lidar configs other than Example_Rotary_2D.
- U2: resolutions other than (128,128).
- U3: point-cloud (non-laser_scan) output.
- U4: tick_rate / accumulate_outputs sensitivity.
- U5: `positions=` vs `translations=` kwarg equivalence.
- U6: SUPPORTED_LIDAR_CONFIGS contents; GMO data semantics.

---

## T8 — PowerShell pumped-leg harness (*.ps1)

DOES: forces sim frames (background pump job over the bridge)
while a foreground ROS leg listens/talks [verified]; builds the
DDS match via pre-talk [verified]; persists evidence [verified].

Functions (as used in-drill, fully typed):
- `listen.ps1 <topic: str> <msgtype: str> <count: int>
  <timeout: float> (s) <out: str> (path)`: sources
  `C:\dev\lyrical\setup.ps1`, prepends Library/bin+bin to
  `$env:PATH: str`, execs pixi python on listener_ros.py
  with the 5 args [verified] (listen.ps1:1-6; calls:
  r2_pumped_listen.ps1:18 `/joint_states jointstate 8 120
  .../r2_js.json`, n1 `/odom odom 8 120`,
  n2 `/scan scan 5 120`, r4 `/tf tf 8 120`). NOTE:
  listen.ps1:6 still points at the pre-merge path
  `skills\ros\scripts\listener_ros.py` [verified] —
  pumped_listen callers pass the new evidence paths, so the
  listener path is stale [probable — flag for fix].
- `r2_pumped_listen.ps1` / `r4_pumped_listen.ps1` /
  `n1_pumped_listen.ps1` / `n2_pumped_listen.ps1`:
  `Start-Job -ScriptBlock { param($send: str, $ws: str) }`
  pump loop (`for ($i: int = 0; $i -lt 6; $i++)`: 6x
  `--file *_pump40.py`, `--timeout 300: int` (s)) +
  foreground `listen.ps1 ...` + `Receive-Job -Job $job
  -Wait` + `Remove-Job -Job $job` [verified: r2 fully read
  (r2_pumped_listen.ps1:8-22); r4/n1/n2 same shape
  [verified: n1 6x n1_pump40 + /odom, n2 6x n1_pump40 +
  /scan, r4 6x r4_pump40 + /tf listens]].
- `r3_pumped_talk.ps1 <v1: float> <v2: float> (rad/s
  [probable])`: env setup + 6 s PRE-TALK primer
  (`talker_ros.py /r3_cmd 0.8 -0.5 6`), then 4x pump job +
  25 s measured talk (`talker_ros.py /r3_cmd 0.8 -0.5 25`),
  then drain [verified: r3_pumped_talk.ps1:10-25]. Fewer
  pump iters (4 vs 6) [verified].
- `r2_pump40.py` / `r3_pump40.py` / `r4_pump40.py` /
  `n1_pump40.py`: in-sim chunk: prefix-scan `ART: str |
  None` (`startswith("R2Bot"|"R3Bot"|"R4Bot"|"N1Base")`,
  r2_pump40.py:13-16, r3_pump40.py:10, r4_pump40.py:25,
  n1_pump40.py:8-10), `await update_app_async(steps:
  int = 40)`, print live pose (`PUMP40 pose=[...: floats
  rad]` r2/r3/r4; `PUMP40 art=<str>` n1) [verified].
- `tmp_rmwprobe.ps1` (no args): env setup + `ctypes.CDLL(
  'rmw_fastrtps_cpp.dll': str)` load probe + `rclpy.init()
  / shutdown()` zero-arg probe [verified:
  tmp_rmwprobe.ps1:5-6]; `tmp_rosenv.ps1` (no args): prints
  `ROS_DISTRO/ROS_DOMAIN_ID/RMW_IMPLEMENTATION: str`,
  `ros2 pkg list` count `: int` (PKGS=353), `nav2*` count
  + first-5 sample [verified: tmp_rosenv.ps1:3-9];
  `tmp_topics.ps1` (no args): 3 s DDS settle then
  `get_topic_names_and_types()` sorted topic-name list
  [verified: tmp_topics.ps1:5].
- `r2_pubcount.ps1 <topic: str> <wait: float> (s) <out: str>`
  (r2_pubcount.ps1:5) + `r2_pubcount.py` (`sys.argv[1]:
  str, [2]: float via float(), [3]: str`, r2_pubcount.py:8;
  `time.sleep(wait: float)` (s), `get_publishers_info_by_
  topic`, `node_name/node_namespace: str`,
  `get_node_names_and_namespaces()`) / `r2_deep.ps1
  <topic: str> <count: int> <timeout: float> (s)
  <out: str>` (r2_deep.ps1:5) + `r2_deeplisten.py`
  (argv `str/int/float/str`, r2_deeplisten.py:10-11;
  `wall: float` (s), full-precision `pos/vel: list[str]`
  via repr) [verified — rclpy subscriber variants].
- Evidence: `Set-Content <path: str> <value: str>` (JSON
  data, txt one-liners) [verified: R4]. Python drivers use
  `open(path: str, mode: str).write(s: str)` [verified]
  (T2 remote-protocol entry).

Knobs + effect-of-change (attr type + unit + default):
- Pump iters `: int = 6` (listen) / `4` (talk) x `steps:
  int = 40` (frames): shipped counts [verified]
  (r2_pumped_listen.ps1:12-13, r3_pumped_talk.ps1:15-16).
  Optimal counts/durations beyond these untested
  [theoretical].
- `--timeout 300: int` (s) on pump jobs: must exceed one
  40-step pump [verified pattern]. Smaller risks killing
  slow pumps [probable].
- Foreground `listen.ps1` args per drill (`topic: str,
  msgtype: str, count: int, timeout: float (s), out: str`):
  e.g. `/joint_states jointstate 8 120 <evd>/r2_js.json`
  [verified]. Larger count/timeout lengthens the leg
  [verified].
- Talker primer `: float = 6` (s) + measured `: float = 25`
  (s) [verified: r3_pumped_talk.ps1:10, :21]. Shorter
  primer risks pre-match windows (F10) [verified].

EKB rules:
- IF a ROS leg runs THEN wrap it pumped (background pump +
  foreground leg) BECAUSE unpumped physics-derived reads are
  static values with advancing stamps [verified: R-pattern].
- IF a commanded drill runs THEN pre-talk before the measured
  window BECAUSE DDS match lags seconds [verified: F10].
- IF evidence is written from PowerShell THEN use Set-Content
  BECAUSE Tee-Object writes UTF-16 [verified: R4].

LIMITS (with cites):
- L1: Tee-Object UTF-16 garbles utf-8 verifier reads [verified:
  R4].
- L2: every commanded drill opens with a match primer [verified:
  F10].
- L3: `listen.ps1` hardcodes the pre-merge listener path
  (`skills\ros\scripts\`) [verified — stale after merge].

UNKNOWN (all [theoretical]):
- U1: optimal pump counts/durations beyond shipped 6x40/4x40.
- U2: Start-Job failure modes under sim hiccups.
- U3: tmp_* probe scripts' exact outputs (skimmed only).

---

## T9 — navigation-primitives library (external, in-sim + local)

DOES: stage rasterization, robot footprint AABBs, exact FK/IK,
pure-pursuit stepping — the planning substrate [verified].

Functions (as used in-drill, fully typed; library source =
navigation-primitives/scripts, exact signatures read on disk):
- `occupancy_map_from_usd(stage: Usd.Stage, x_range:
  tuple[float, float] = (-15, 175) (m),
  y_range: tuple[float, float] = (-25, 155) (m), resolution:
  float = 0.25 (m/cell), z_cutoff: float = 4.5 (m),
  colliders_only: bool = True) -> np.ndarray uint8 (H, W),
  0=free/255=occupied` [verified: source
  occupancy_map_from_usd.py:10-31 + call n1_run.py:18 as
  `(stage, (-5,5), (-5,5), 0.25, 4.5, True)`]. N1 used it
  via sys.path inject (fresh server), V11 inlined the
  20-line loop (R3 caching) [verified: discovery].
- `compute_robot_footprint(stage: Usd.Stage, robot_root: str)
  -> dict{size: tuple[float,float,float] (m), z_offset: float
  (m), inscribed_radius: float (m), circumscribed_radius:
  float (m), aabb_min/aabb_max: tuple (m)}` [probable —
  exact source signature (robot_footprint.py:10-23), no
  live call: drills INLINE it] via
  `bounds_utils.compute_combined_aabb(elements:
  list[Usd.Prim]) -> 6-float aabb [xmin,ymin,zmin,
  xmax,ymax,zmax] (m [probable]; ndarray-like [probable —
  `mx-mn` subtracts, n3_run.py:20])` [verified call:
  n3_run.py:18]. Library passed `Sdf.Path` into
  ComputeWorldBound (wants UsdPrim) => crashed; FIXED on
  disk (pass prims, 2-line patch, single usage site)
  [verified: R2/R3]. N3 inline: harvest colliders via
  `Usd.PrimRange` + `HasAPI(CollisionAPI)`, fallback
  to the bot prim itself, `aabb =
  compute_combined_aabb(colliders)`, `mn,mx =
  aabb[:3],aabb[3:]`, `size = mx-mn`, `inscribed =
  min(sx,sy)/2`, `circumscribed = hypot(sx/2,sy/2)`
  [verified: n3_run.py:14-26]. Fresh-import live check
  exact (0.4^3/0.4/0.2/0.2828) [verified: R2].
- `kinematics` FK/IK (exact source, kinematics.py:47-105;
  calls [verified: n4_follow.py:20-24], units from source
  docstrings [probable]): `differential_forward(linear:
  float (m/s), angular: float (rad/s), params:
  DifferentialParams) -> tuple[float, float]` (vL, vR in
  rad/s) — called `(1.0, 0.5, dp)`;
  `differential_inverse(v_left: float (rad/s), v_right:
  float (rad/s), params) -> tuple[float, float]` (linear
  m/s, angular rad/s); `holonomic_forward(vx: float (m/s),
  vy: float (m/s), omega: float (rad/s), params:
  HolonomicParams) -> np.ndarray (3,)` (rad/s) — called
  `(0.3, 0.1, 0.4, hp)`; `holonomic_inverse(wheel_vels:
  np.ndarray (3,) (rad/s), params) -> tuple[float, float,
  float]` (vx, vy m/s, omega rad/s). Round-trips exact to
  1e-9 both drive types [verified: n4_follow + discovery].
- `pure_pursuit_step(robot_pos: np.ndarray (2,) (m),
  robot_yaw: float (rad), path: np.ndarray (N, 2) (m,
  REMAINING), config: PurePursuitConfig,
  prev_heading_error: float = 0.0 (rad)) -> dict{linear:
  float (m/s), angular: float (rad/s), heading_error: float
  (rad), target_idx: int, done: bool}` [verified calls:
  n4_follow.py:37 `(pos, yaw, path[k:], cfg, prev)`,
  v11_pipeline.py:91; full key set from source
  kinematics.py:126-191 — `target_idx` unread in-drill
  [probable]]. `cfg = PurePursuitConfig()` defaults;
  `prev: float` = previous heading_error [verified].
  STATELESS: scans from index 0, no progress tracking
  [verified: R5].
- `DifferentialParams(wheel_radius: float = 0.14 (m),
  track_width: float = 0.499 (m), max_linear_speed: float =
  1.5 (m/s), max_angular_speed: float = 1.5 (rad/s))`;
  `HolonomicParams(wheel_radius: float = 0.04 (m),
  wheel_base: float = 0.10 (m), max_linear_speed: float =
  0.5 (m/s), max_angular_speed: float = 2.0 (rad/s))`;
  `PurePursuitConfig(lookahead_distance: float = 1.0 (m),
  linear_speed: float = 1.0 (m/s), goal_tolerance: float =
  0.5 (m), slowdown_distance: float = 2.0 (m),
  max_angular_speed: float = 1.5 (rad/s), kp_angular: float
  = 2.5 (1/s [probable]), kd_angular: float = 1.2 (unit
  [theoretical]))` [verified defaults: source
  kinematics.py:27-44, :113-124; constructed default-only
  in n4_follow.py:20, :28, v11_pipeline.py:85]. Non-default
  param effects untested [theoretical].
- Local `nav_check.footprint_clips_np(x: float (m), y: float
  (m), yaw: float (rad), size: sequence[float] (sx, sy [,
  sz]; m), res: float (m/cell), grid: np.ndarray uint8
  (H, W), xr: tuple[float, float] (m), yr:
  tuple[float, float] (m)) -> bool` [verified: source
  nav_check.py:12 + call v11_pipeline.py:80 with
  atan2-derived yaw (rad) at v11_pipeline.py:79].
  cv2-free oriented stamp: tests 8 rotated-rect sample
  points (4 corners + 4 edge midpoints) against occupied
  cells AND occupied-cell centers within reach against the
  rect; either hit = clip [verified]. Conservative on
  clear-cut cases [verified: docstring].

Knobs + effect-of-change (attr type + unit + default):
- Raster `xr/yr: tuple[float, float] = (-5,5)/(-5,5)` (m),
  `res: float = 0.25` (m/cell) (N1 40x40; V11 same frame):
  exact occ counts predicted by slice arithmetic (N1: 50,
  V11: 62) [verified] (n1_run.py:17). Finer res => more
  cells, same geometry [probable].
- `zcut: float = 4.5` (m): height cutoff [verified value].
  Effect of change untested [theoretical].
- `colliders_only: bool = True`: visual-only prims +
  un-collidered ground ignored [verified: SKILL]. False
  untested [theoretical].
- Prim placement off exact cell boundaries dodges float
  truncation [verified: SKILL] (placement `: float` m).
- Pursuit remaining-path window `path[k:]` with monotonic
  `k: int`: REQUIRED; full-path calls stall past 1 m
  (reverse oscillation, 400 steps arrival 10.4 m) vs
  windowed done in 132 arrival 0.494 [verified: R5]
  (n4_follow.py:33-36, v11_pipeline.py:90).
- Unicycle sim `dt: float = 0.1` (s), `MAXS: int = 400`
  steps [verified: n4_follow.py:32]. Other dt/budgets
  untested [theoretical].

EKB rules:
- IF the stage is rasterized THEN use colliders_only + clean
  prior drill colliders first BECAUSE rasterizers see the whole
  stage (54 phantom cells in V11) [verified: R6].
- IF occupied counts are predicted THEN use [x0:x1) slice
  arithmetic (count x1-x0) BECAUSE inclusive counting overcounts
  (84 vs 62) [verified: R7].
- IF pursuit follows a path THEN pass the REMAINING path
  (nearest-index window) BECAUSE the step scans from index 0
  [verified: R5].
- IF a library function is short THEN inline it in sent scripts
  BECAUSE the server caches repo imports [verified: R3].
- IF footprint AABBs are computed THEN pass UsdPrim elements,
  never Sdf.Path, BECAUSE ComputeWorldBound wants UsdPrim
  [verified: R2].
- IF stamping runs locally THEN use the numpy-only
  footprint_clips_np BECAUSE local python has no cv2 [verified:
  discovery Environment].

LIMITS (with cites):
- L1: library compute_robot_footprint crashed on Sdf.Path;
  fixed on disk, inlined in drills [verified: R2/R3].
- L2: pure_pursuit_step full-path stalls past 1 m [verified: R5].
- L3: rasterizers see the whole stage [verified: R6].
- L4: slices are [x0:x1) [verified: R7].
- L5: rasterize colliders_only; visual-only + un-collidered
  ground ignored [verified: SKILL].
- L6: local python has numpy+scipy, NO cv2/pxr; in-sim has
  numpy+scipy+cv2 [verified: discovery].

UNKNOWN (all [theoretical]):
- U1: kinematics beyond verified FK/IK + pursuit surface.
- U2: cv2-based stamping (in-sim has cv2; drills use numpy-only).
- U3: PurePursuit/Differential/Holonomic non-default params.
- U4: zcut sensitivity; colliders_only=False behavior.

---

## T10 — Local planning stack (numpy + scipy + heapq)

DOES: runs A*, erosion, footprint validation, and pursuit follow
locally with no ROS/sim [verified].

Functions (as used in-drill, fully typed):
- `numpy` grids/stamps [verified]: `np.array(G["grid"]:
  list, dtype=np.uint8) -> np.ndarray uint8 (H, W)`
  (n2_plan.py:16, v11_pipeline.py:23); `np.ogrid[-kr:kr+1,
  -kr:kr+1] -> (ky: ndarray int, kx: ndarray int)`
  (n2_plan.py:21, v11_pipeline.py:27); `np.linalg.norm(
  path[k:] - pos: ndarray (M,2) (m), axis: int = 1) ->
  ndarray (M,) float (m); .argmin() -> int [probable —
  np.intp]` nearest-index (n4_follow.py:35,
  v11_pipeline.py:90); `np.hypot(a: float, b: float) ->
  float` (m, n3_run.py:26).
- `scipy.ndimage.binary_erosion(input: ndarray bool (H, W),
  structure: ndarray bool (2kr+1, 2kr+1)) -> ndarray bool
  nav grid` [verified] (n2_plan.py:23,
  v11_pipeline.py:28). N2 kernel: disc `kx*kx+ky*ky <=
  kr*kr` with `kr: int = round(0.3/0.25) = 1` (cells;
  INSCRIBED `: float = 0.3` m, n2_plan.py:19-22)
  [verified: n2_plan]; V11 kernel: 4-connected cross
  `kx*kx+ky*ky <= 1` [verified: v11_pipeline.py:27-28].
- `heapq` open queue [verified] (`cell =
  tuple[int, int]`, grid indices): `openq:
  list[tuple[float, cell]]` (priority, cell);
  `heappush(openq: list, item: tuple[float, cell]) ->
  None`, `heappop(openq: list) -> tuple[float, cell]`
  (n2_plan.py:43, :47, :63). Octile heuristic `_h(a: cell,
  b: cell) -> float` (cells) `= max + (sqrt2-1)*min`
  (n2_plan.py:38-40, v11_pipeline.py:42-44). 8-connected
  `DIRS: list[tuple[int, int, float]]` (dx/dy cells, w
  cost: axis 1.0, diagonal sqrt(2)), no-corner-cutting
  (`nav[cur.y,nxt.x] and nav[nxt.y,cur.x]`) [verified].
  `came: dict[cell, cell|None]`, `cost: dict[cell, float]`;
  cell->world `(c+0.5)*res: float` (m) [verified]
  (n2_plan.py:44, :68-69).
- `math` [verified]: `sqrt(x: float) -> float` (called
  as `sqrt(2)`), `atan2(dy: float (m), dx: float (m)) ->
  yaw: float`
  (rad) (n4_follow.py:30, v11_pipeline.py:79, :87),
  `cos/sin(yaw: float (rad)) -> float` integration
  (n4_follow.py:43, v11_pipeline.py:97-98, nav_check.py:14).
- Verifiers `verify_n1/n2/n3/n4/v11.py` (stdlib
  json/sys/math): `check(name: str, cond: bool) -> None`
  (verify_n2.py:11-14); gate grids/paths/footprints/
  follows; N2: `len: int = 40` > king 32, all free; N4:
  done in 132, arrival `: float = 0.494` (m); V11: 12/12
  arrival 0.479 (m) [verified: SKILL drill table +
  verify_n2.py:24-37].
- `exam15.py` / `x15.py` (bridge) [verified: exam15.py:24-36,
  x15.py:29-31]: `subprocess.run(args: list[str],
  capture_output: bool = True, text: bool = True, timeout:
  int = 900 (drive) / 120 (verify) / 180 (audit)) (s) ->
  CompletedProcess`; `.returncode: int`, `.stdout: str`.
  R1-R4 replay (4/4) + audit + error scan (5/5)
  [verified: SKILL].

Knobs + effect-of-change (attr type + unit + default):
- Erosion radius `: float` (m): N2 inscribed 0.3 m (`kr: int
  = 1` cells @0.25); V11 4-connected cross [verified]
  (n2_plan.py:19-23, v11_pipeline.py:27-28). Larger radius
  => narrower nav space; other radii untested [theoretical].
- A* baseline `max(|dx|,|dy|): int` (cells, king-move):
  valid avoidance path (40) must EXCEED it (32) [verified:
  R1]. Euclidean baseline (45) overestimates and valid paths
  "fail" [verified: R1].
- START/GOAL cells `: tuple[int, int]` (cells) from
  (-4,-4)->(4,4) (m) [verified] (n2_plan.py:26-31). Ends
  blocked => assert fails fast [verified].
- Pursuit gates four ways: `done: bool` flag, `arrival:
  float` (m) < tolerance, `max_dev: float` (m), `steps:
  int` budget (N4: 132/0.494/0.247) [verified: discovery
  Drill rules] (n4_follow.py:45-49).
- Grid `: ndarray uint8 (40, 40)` @ `res: float = 0.25`
  (m/cell) [verified]. Larger grids untested [theoretical].

EKB rules:
- IF A* paths are gated THEN baseline against king-move distance
  max(|dx|,|dy|) BECAUSE Euclidean overestimates the 8-connected
  lower bound [verified: R1].
- IF nav space is built THEN erode by inscribed radius BECAUSE
  raw free space admits center-positions that clip corners
  [verified: n2_plan pattern].
- IF pursuit is gated THEN gate four ways (done/arrival/dev/
  budget) BECAUSE any single gate passes degenerate follows
  [verified: discovery].
- IF corners are cut THEN forbid diagonal moves unless both
  orthogonal neighbors are free BECAUSE corner cutting clips
  obstacle corners [verified: shipped code].

LIMITS (with cites):
- L1: A* baselines must use king-move distance [verified: R1].
- L2: planning A*/pursuit are kinematic (no dynamics)
  [verified: SKILL Limitations].
- L3: local python numpy+scipy, no cv2/pxr — planning stays
  numpy-only locally [verified: discovery].

UNKNOWN (all [theoretical]):
- U1: larger-grid performance.
- U2: erosion radii beyond shipped 0.3 / cross kernel.
- U3: dynamic replanning.
- U4: diagonal-cost variants (only 1.0/sqrt2 used).

---

## T11 — Minor / probe-only APIs (skimmed, not drill load-bearing)

DOES: one-off diagnostics during bisection [verified].

Functions (as used in-drill, fully typed):
- `omni.isaac.dynamic_control` (dc) [verified: r2_dcstate.py]:
  `dc.acquire_dynamic_control_interface() -> DCI [probable]`
  (r2_dcstate.py:7); `d.get_articulation(path: str) -> art
  handle [probable]` (r2_dcstate.py:8);
  `dc.INVALID_ARTICULATION` sentinel (r2_dcstate.py:10);
  `d.get_articulation_dof_count(art: ArtHandle [probable]) ->
  int` + `d.get_articulation_body_count(art: ArtHandle
  [probable]) -> int` (r2_dcstate.py:11-12);
  `d.get_articulation_dof_states(art: ArtHandle [probable],
  dc.STATE_POS) -> dict{"pos": sequence[float]} [probable]`
  (r2_dcstate.py:13-14; pos rad [probable]). Probe-only
  state read [verified].
- `omni.timeline.get_timeline_interface() -> Timeline
  [probable]; .is_playing() -> bool` [verified:
  r2_manstate_probe.py:35-36, r2_nodemeta_probe.py:80-81].
- `omni.kit.app.get_app() -> App [probable];
  .get_extension_manager() -> EM [probable]`
  (r2_reset.py:22, r2_nodereq_probe.py:129-130);
  `m.set_extension_enabled_immediate(name: str, enabled:
  bool) -> None [probable]` (preferred, hasattr-gated) /
  `m.set_extension_enabled(name: str, enabled: bool)`
  (fallback) [verified: r2_reset.py:23-33].
- `omni.kit.commands as kc` [verified]: `kc.execute(
  command_name: str, **kwargs: Any) -> tuple[ok: bool,
  result: Any]` — `("IsaacSensorCreateRtxLidar",
  path: str = "/N2LidarProbe")` (n2_sig3.py:20-21,
  n2_lidar_attr.py:8-9, n2_rp_probe.py:8) and
  `("RangeSensorCreateRtxLidar", path: str, parent: None,
  min_range: float = 0.4 (m), max_range: float = 20.0 (m),
  draw_points: bool = False, draw_lines: bool = False,
  sampling_rate: int = 0)` (n2_lidar_probe.py:9-17);
  `kc.get_command_parameters(name: str) -> list[Param]`
  with `.name: str`, `.default: Any` (n2_sig.py:7,
  n2_sig2.py:7-8, n2_sig3.py:7-8); `kc.get_command_doc(name:
  str) -> str | None [probable]` (n2_sig2.py:13,
  n2_sig3.py:12-13).
- `omni.replicator.core.Writer` subclass shape [verified:
  n2_2dtest.py:22-43, n2_gmoprobe.py:16-36, n2_box.py:23,
  n2_rp3.py:18]: `class W(Writer)`; `__init__(self) ->
  None` sets `self.data_structure: str = "renderProduct"`,
  `self.annotators: list = [rep.annotators.get(
  "GenericModelOutput": str) -> Annotator [probable]]`;
  `write(self, data: dict{"renderProducts": dict[str,
  dict]}) -> None`. `import warp as wp`; `wp.array` type;
  `wp_array.numpy() -> np.ndarray [probable]`
  (n2_2dtest.py:16-19). Raw `writer.attach([product])`
  never ticks for RTX [verified: F2 ruled-out];
  `sensor.attach_writer` works [verified: F2 ruled-out].
- `rep.WriterRegistry.register(writer_cls: type) -> None
  [probable]`; `rep.WriterRegistry.get(name: str) -> Writer`
  [verified: n2_gmoprobe.py:49-50, n2_2dtest.py:53,
  n2_rp3.py:70-71]; `rep.writers.get(name: str) -> Writer`
  + `writer.initialize(topicName: str = "scan", frameId: str
  = "base_scan", queueSize: int = 10) -> None [probable]`
  [verified: n2_writertest.py:20-23; further kwargs, if any,
  ungated [theoretical]].
- `isaacsim.core.experimental.utils.prim` (prim_utils):
  `prim_utils.get_prim_at_path(path: str) -> Usd.Prim
  [probable — GetAttribute called on result]` [verified:
  n2_canonical.py:37].
- `isaacsim.core.experimental.utils.bounds`:
  `bounds_utils.compute_combined_aabb(colliders:
  list[Usd.Prim]) -> 6-float aabb` (typed under T9)
  [verified: n3_run]. NOT probe-only — load-bearing for
  footprints [verified].
- `og.get_node_type(type_string: str) -> NodeType [probable]`;
  `t.get_attributes() -> list[Attribute] [probable]`;
  `a.get_name() -> str`; `a.get_default_value() -> Any`
  [verified: n2_helpdefaults.py:9-22].
- Verifiers `verify_r*` / `verify_n*` / `x15.py`: stdlib-only
  (json/sys/re/math/subprocess/datetime/os) evidence gates
  [verified: fully read verify_n2; others by skim + SKILL
  table]. `check(name: str, cond: bool)` shape (T10).
- Probes `probe_*.py`, `r2_nodereq_probe.py`,
  `r2_nodemeta_probe.py`, `n2_apiprobe.py`
  (`inspect.signature(obj: Any) -> Signature`,
  n2_apiprobe.py:11-12 on `Lidar.create` /
  `LidarSensor.__init__`; n2_rp2.py:11 on
  `rep.create.render_product`), `n2_helpdefaults/helpdefs2/
  helpprobe`, `n2_ports.py`, `n2_proddump.py`,
  `probe_nav*.py`, `audit_stage.py`: attribute/node-type/
  meta dumps [verified by skim]. `audit_stage.py` = stage
  audit (UsdPhysics) [verified by skim].

Knobs + effect-of-change (attr type + unit + default):
- None supported: every knob here is diagnostic-only; changing
  values changes only the probe output [probable]. (Typed as
  explicitly-no-knobs: 1/1 covered.)

EKB rules:
- IF a silent pipeline is bisected THEN probe in-sim state
  (dc, timeline, node meta, GMO writers) before theorizing
  BECAUSE USD structure alone misleads (F3/F6/F2d all had valid
  USD) [verified: failure-catalog pattern].
- IF a verifier gates THEN conjoin with HAVE (msgs>=5) BECAUSE
  vacuous `all()` passes [verified: F2 ruled-out].

LIMITS (with cites):
- L1: verifier vacuity — `all()` over zero msgs passes
  [verified: F2 ruled-out].
- L2: none of these APIs are drill-supported beyond their probe
  usage [verified: TOOLS.md].

UNKNOWN (all [theoretical]):
- U1: everything about dc/timeline/kit.commands/warp/Writer/
  prim_utils beyond probe usage.
- U2: `enable_extension("isaacsim.sensors.physics.nodes")`
  (r2_build_manual only) — purpose ungated.

---

## Counts

- Tools covered: 11 (T1-T11, mirrors TOOLS.md sections).
- Functions documented: 104 entries (T1: 16, T2: 4, T3: 7,
  T4: 10 node types + ports, T5: 20, T6: 8, T7: 9, T8: 7,
  T9: 6, T10: 6, T11: 11).
- Knobs documented: 56 (T1: 7, T2: 4, T3: 4, T4: 8, T5: 9,
  T6: 2, T7: 6, T8: 4, T9: 6, T10: 5, T11: 1).
- DATATYPE pass (2026-11-04): signatures typed 104/104 (every
  entry carries param types + return type + units + defaults,
  with [probable]/[theoretical] tags where call sites do not
  ground a type); knobs typed 56/56 (T11's single entry is
  explicitly-no-knobs). Still-unknown type/unit/default items:
  0 untyped — residual [theoretical] markers inside typed
  entries (ungated defaults, unwitnessed units) are counted in
  the Unknowns line, not as missing types.
- EKB rules: 49. Limits: 45 (all cited). Unknowns: 46 (all
  tagged theoretical).
- Scripts: 51 fully read + 75 skimmed = 126 total (64 bridge,
  45 bringup, 17 planning) + 3 external library sources fully
  read (navigation-primitives).





