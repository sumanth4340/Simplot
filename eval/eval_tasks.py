"""Eval task set: unseen wordings the model never trained on.

8 action tasks (expect catalog action lines) + 4 dispatch tasks
(expect a deploy plan). Snapshots are canned; expect_skill pins the
retrieval behavior the suite locks in (run score.py to re-pin after a
deliberate routing change).
"""
SNAPSHOT_EMPTY = "sim: paused\nstage has no /World"

TASKS = [
    {"id": "EA1", "kind": "action",
     "task": "author a green cone prim on the USD stage",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "stage"},
    {"id": "EA2", "kind": "action",
     "task": "assemble a moon rover and drive it forward",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "nav2"},
    {"id": "EA3", "kind": "action",
     "task": "sweep the room with a spinning lidar",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "isaac-sim-sensor"},
    {"id": "EA4", "kind": "action",
     "task": "set the rigid body mass of the steel crate",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "physics"},
    {"id": "EA5", "kind": "action",
     "task": "create fixed cylinder prims and a visual marker on the USD stage",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "stage"},
    {"id": "EA6", "kind": "action",
     "task": "set angular drive torque limits on the elbow articulation joints",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "articulation"},
    {"id": "EA7", "kind": "action",
     "task": "set lunar gravity and reset the trial",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "physics"},
    {"id": "EA8", "kind": "action",
     "task": "bring in the robot URDF and save the stage",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "modeling"},
    {"id": "ED1", "kind": "dispatch",
     "task": "drive the lidar rover across the arena to the goal",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "rosnav"},
    {"id": "ED2", "kind": "dispatch",
     "task": "grasp the heavy crate with the arm and palletize it",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "manipulation"},
    {"id": "ED3", "kind": "dispatch",
     "task": "capture a labeled KITTI sweep of the warehouse floor",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "sdg-adv"},
    {"id": "ED4", "kind": "dispatch",
     "task": "step the timeline, pause, and undo the bad prim",
     "snapshot": SNAPSHOT_EMPTY, "expect_skill": "pyapi"},
]
