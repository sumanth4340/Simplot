# R2 ROS2PublishJointState node requirements (verified in-sim)

Date: 2026-11-03. Sim: Isaac Sim 6.x windowed (`c:/isaacsim`),
ext `isaacsim.ros2.nodes`, node v1 (C++).
Doc source: `C:/isaacsim/exts/isaacsim.ros2.nodes/ogn/docs/OgnROS2PublishJointState.rst`
+ live probes (all claims below verified in-sim unless marked).

## TL;DR

- The node is fine and the current R2 wiring is fine. `/joint_states`
  from `/ROS2/R2` (targetPrim-only) IS advertised and streams live data
  during play (verified: 5 msgs, names `[J1, J2]`, increasing sim stamps).
- The "topic never appears + zero errors" symptom is a LISTENER-side
  artifact, not a publisher defect (see "Root cause" below).
- Preferred data path per the node's own doc: connected joint arrays
  from `isaacsim.sensors.physics.IsaacReadJointState`
  ("connect instead of targetPrim for preferred path"). Verified working.
- Literal (unconnected) values on jointNames/jointPositions/... do NOT
  work: no publisher is created even with all five arrays set,
  timestamp wired, and a fresh replay.

## Node inputs (from live prim dump + .rst doc)

| Input | Type | Default | Notes (verified) |
|---|---|---|---|
| `inputs:execIn` | execution | — | Drive from `OnPlaybackTick.outputs:tick` |
| `inputs:timeStamp` | double | 0.0 | ROS2 stamp (s). Used by targetPrim path |
| `inputs:topicName` | string | `joint_states` | R2 uses `/joint_states`; works |
| `inputs:queueSize` | uint64 | 10 | 10 works |
| `inputs:targetPrim` | target (rel) | None | Auto-read path: point at articulation root |
| `inputs:jointNames` | token[] | [] | MUST be connected (reader node), see below |
| `inputs:jointPositions` | double[] | [] | rad or m; connected |
| `inputs:jointVelocities` | double[] | [] | rad/s or m/s; connected |
| `inputs:jointEfforts` | double[] | [] | Nm or N; connected |
| `inputs:jointDofTypes` | uchar[] | [] | 0=revolute, 1=prismatic; connected |
| `inputs:sensorTime` | float | 0.0 | "used as message timestamp when connected" |
| `inputs:stageMetersPerUnit` | float | 0.0 | SI conversion, from reader node |
| `inputs:context` | uint64 | 0 | 0 = default global context. Leave unset (same as working clock node) |
| `inputs:nodeNamespace` | string | "" | Leave unset |
| `inputs:qosProfile` | string | "" | Leave unset |

No `outputs:*` on the publisher. Context/QoS/namespace need no setup.

## Working wiring 1: targetPrim auto-read (current R2 graph, VERIFIED)

`/ROS2/R2`: `OnPB.tick -> JS.execIn`,
`Time.simulationTime -> JS.timeStamp`, `topicName=/joint_states`,
`queueSize=10`, rel `inputs:targetPrim -> /World/R2Bot`.
Target prim requirements (verified): valid prim with
`UsdPhysics.ArticulationRootAPI` and ≥1 physics joint underneath
(R2Bot: root API present, J1+J2 `PhysicsRevoluteJoint`, correct
body0/body1). No reader node, no arrays needed.

Evidence: `ros2 topic list` during play shows `/joint_states`;
`evidence/r2_orig_js.json` = 5 msgs, names `[J1, J2]`, stamps
160.16→160.23 increasing.

## Working wiring 2: explicit CONNECTED arrays via IsaacReadJointState (VERIFIED)

Reader: `isaacsim.sensors.physics.IsaacReadJointState`
(ext `isaacsim.sensors.physics.nodes`, doc `OgnIsaacReadJointState.rst`).
Inputs: `execIn`, `inputs:prim` (target rel → articulation root).
Outputs: `execOut` ("triggers when sensor has data"), `jointDofTypes`,
`jointEfforts`, `jointNames`, `jointPositions`, `jointVelocities`,
`sensorTime`, `stageMetersPerUnit`.

Minimal wiring: `OnPB.tick -> Read.execIn`, `Read.execOut -> Pub.execIn`,
all 7 reader outputs -> matching `Pub` inputs, `topicName`, `queueSize`.
`timeStamp` optional (sensorTime stamps the message). No targetPrim.

Evidence: test graph `/ROS2/R2MAN` (since removed) on
`/joint_states_manual` → `evidence/r2_man_js.json` = 5 msgs,
names `[J1, J2]`, stamps increasing. Same articulation, same session.

## NOT working: literal array values (VERIFIED negative)

`jointNames=[J1,J2]` (+positions, then +velocities, then +dofTypes
+efforts, then +wired sensorTime/timeStamp, each followed by a fresh
stop→play) never creates a publisher: topic absent from
`ros2 topic list` across two graphs (`/ROS2/R2MAN/PubStatic`,
`/ROS2/R2STAT/JS`, both since removed). The node needs UPSTREAM
CONNECTIONS on the array inputs (or targetPrim); USD fallback values
are ignored. So a "static arrays" fallback is impossible — the viable
fallback is wiring 2 (reader node), implemented in
`../scripts/r2_build_manual.py` (same wiring as verified, topic
`/joint_states`; drop-in rebuild of `/ROS2/R2`; NOT executed —
parent decides when to switch).

## Root cause of the reported symptom (VERIFIED)

Not the node. A ROS listener whose DDS transport is blocked
reproduces the exact report: no topics, zero errors. Proof by control:
same listener, same sim, same play window — sandboxed run hears
NOTHING (not even `/clock`; FastDDS SHM "Access is denied" on stderr),
network-enabled run hears `/clock` (3 msgs), `/joint_states` (5),
`/joint_states_manual` (5). Fix: re-run the R2 listen step with
network access (the escalated run used here) and `/joint_states`
appears. Also note publishers only exist during play; a topic list
taken while stopped is legitimately empty.

## Observations for parent (out of my scope, not acted on)

- Joint positions in received msgs were static (`[0.0036, -0.0123]`
  across windows) despite J1's 0.5 rad/s velocity drive. Publishing
  works; motion does not (yet). Articulation untouched per orders.
- `Articulation("/World/R2Bot")` (experimental prims API) raised
  `object of type 'NoneType' has no len()` in my probe, yet both the
  reader node and targetPrim auto-read return 2 live DOFs — treat the
  prims-API error as probe/API misuse, not an articulation defect.
- Live-edit note: `og.Controller.edit` with dict `graph_path` fails on
  an existing graph while playing ("Failed to wrap graph"); use
  `og.Controller.connect(...)` / USD attribute `Set(...)` instead.
- End state: test graphs removed, sim STOPPED, `/ROS2/R2` and
  `/World/R2Bot` untouched and valid. `r2_build.py`, `r2_drive.py`
  unmodified. My verification listen artifacts: `r2_man_js.json`,
  `r2_orig_js.json`, `r2_static_js.json` (stale zeros from blocked
  runs — ignore), `r2_clk_check.json`.
