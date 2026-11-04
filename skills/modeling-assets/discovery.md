# Skill 3 MODELING & ASSETS — Discovery

## Scope
Owns geometry authoring and asset intake: hand-authored meshes, URDF
import, materials + binding, cloning, validation. Reads via Skill 0
sense; composes via Skill 2 mechanics. MJCF/heightmap share the URDF
importer family and are documented stretch, not drilled.

## Competence goals (must pass unaided after training)
1. Author indexed quad meshes (right winding, exact bounds) + color.
2. Import a URDF robot: links, joints, structure verified live.
3. Create PBR materials and bind them; prove binding + values.
4. Clone assemblies N-wide with exact counts.
5. Validate an asset (structure + physics presence) before handoff.

## Drill plan (each: run + local verify + evidence)
- M1 mesh: 2x1x0.5 box mesh, 6 outward-CCW quads, red; bound exact.
- M2 urdf: 2-link arm imported; links + revolute joint verified.
- M3 material: UsdPreviewSurface red, bound; binding + attrs proven.
- M4 clone: 3x3 clone grid; 9 copies sensed.
- V3 exam: import + material + clones + save/reopen round-trip.

## Sources (to be verified live, not trusted)
- Installed: isaacsim.asset.importer.urdf, isaacsim.core.cloner (read
  source before calling; never trust remembered spellings).
- USD: UsdGeom.Mesh, UsdShade material/binding APIs.
