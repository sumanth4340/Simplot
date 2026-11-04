# Skill Agents — appointed roster (standby, spawn on demand)

All 18 agents below are APPOINTED as of 2026-11-04. None run idle: the
Thinker spawns an agent only when a task needs its skill pack, tasks it
with the pack path + objective, and stands it down when done.

## Standing orders (every agent)

1. Read your pack first: `SKILL.md` (or `README.md`), `failures.md`,
   `discovery.md`, `scripts/`, `evidence/` — in that order.
2. Live evidence before theory: on any error, freeze the scene and use
   read-only checks (bridge snapshot, outbox result, screenshot) before
   proposing anything.
3. Report findings + evidence + proposed ACTION LINES. No essay prose.
4. Never invent action keys: only `actions_compact.json` keys; flag
   `NO-HANDLER-YET` keys instead of emitting them.
5. Your lane only: if the job crosses packs, say which agent to call next.
6. Distill before you stand down: PROPOSE the reusable lesson (path +
   section + patch summary) in your report; write it into the pack only
   after the user confirms. No silent skill writes, ever.
7. Output actions first: lead every report with the artifact as
   action/command lines (code block), then labeled findings. Think in
   logic; English only in short labeled bullets. A "create a cube" job
   reports `create.objects.cuboid ...`, not a paragraph.

## Roster

| Agent | Pack | Call when the task involves |
|---|---|---|
| `sense` | `skills/workspace-sense/` | reading stage state, sense maps, what-exists-where |
| `stage` | `skills/stage-core/` | USD prims, layers, references, stage surgery |
| `modeling` | `skills/modeling-assets/` | building meshes, assets, importing models |
| `articulation` | `skills/articulation-robots/` | robot imports, articulations, joints, drives |
| `manipulation` | `skills/manipulation-motion/` | grasping, arm motion, trajectories |
| `rendering` | `skills/rendering-lighting/` | lights, materials, look, viewport capture |
| `viewport` | `skills/viewport-ui/` | cameras, UI, screenshots, overlays |
| `omnigraph` | `skills/omnigraph/` | OmniGraph graphs, ROS2 graph nodes |
| `behavior` | `skills/behavior-anim/` | animation, behavior sequences |
| `appsession` | `skills/app-session/` | app lifecycle, sessions, extensions |
| `physics` | `skills/physics/` | rigid bodies, colliders, mass, gravity, engines |
| `pyapi` | `skills/pyapi/` | Kit commands/undo, file ops, timeline control |
| `deform` | `skills/deform/` | soft bodies, deformables (D1) |
| `gpunuc` | `skills/gpunuc/` | GPU selection, asset roots (G1/G2) |
| `rosnav` | `skills/ros-navigation/` | ROS bridge, nav2 bringup, rover drive (R/N drills) |
| `sensors` | `skills/sensors/` | lidar/radar/ultrasonic, scans (R1/R2) |
| `sdg` | `skills/sdg/` | synthetic data, writers, datasets (A drills) |
| `xval` | `skills/cross-val/` | QA gate: cross-check a build against other packs |

## How tasking works

The Thinker (chat operator or Glimmer) decomposes each user task and
assigns the pieces; agents execute and co-work via declared needs —
single-skill primitives still go straight to action lines. A skill
agent is spawned when a task needs pack knowledge: failure diagnosis,
multi-step procedures from `failures.md`, live-stage evidence
gathering, or owned build/verify work. A job spanning packs declares
its agent dependencies up front (`needs: articulation + physics`).
The `xval` agent is spawned after any multi-pack build to run the
gauntlet. All agent reports lead with action lines (order 7).
