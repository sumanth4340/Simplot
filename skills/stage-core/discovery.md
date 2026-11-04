# Skill 2 STAGE & USD CORE — Discovery

## Scope
Owns the stage itself: new/open/save USD, prim lifecycle, any-property
get/set, layers + sublayers, references/payloads/variants, selection,
undo. Every other master builds on this. Reads via Skill 0 sense.

## Competence goals (must pass unaided after training)
1. New stage / save .usd to disk / reopen it: round-trip exact.
2. Create/delete typed prims (Cube/Sphere/Cylinder/Cone/Torus/Plane).
3. Set/get any property (transform, size, color, visibility, purpose)
   with exact readback.
4. Author an override sublayer; prove via property stack it wins; remove
   it and prove revert.
5. Reference an external .usd, toggle payloads, switch variant sets.
6. Select prims; undo a mutation.

## Drill plan (each: run + local verify + evidence)
- S1 stage round-trip: new -> cube -> save -> new -> open -> cube back.
- S2 prim lifecycle: all 6 types created, sensed, deleted.
- S3 properties: 12-op set/get matrix incl. color/visibility/purpose.
- S4 sublayer override: win + revert proven via property stack.
- S5 reference/variant: external asset referenced, variant switched.
- V2 exam: composed scene from scratch (prims + props + layer + ref).

## Sources (to be verified live, not trusted)
- isaac-sim-remote open_stage.py / prim_properties.py / select_prim.py.
- usd-composition-architecture: precedence, property-stack debugging.
