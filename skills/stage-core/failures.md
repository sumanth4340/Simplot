# Stage Core — Failure Catalog (live-verified)

## L1: opening a saved .usd auto-adds the viewport light rig
- FINDING: Fresh `new` stage has 12 prims; after save + reopen, the same
  stage has 16 + content: Kit injects `/OmniKit_Viewport_LightRig/Lights/`
  with a DomeLight and a DistantLight on file open.
- IMPACT: Prim-count assertions across save/open must allow the 4 rig
  prims. S1 verifies by path-set (fresh set + cube), not raw count.
- NOTE: The rig also means "open file" scenes are never unlit; the fresh
  `new` template has no lights at all.

## L2: sublayers cannot beat the root's own direct opinions
- FAILURE: S4 v1 put the base cube (size 1.0) directly on the root layer
  and stacked an override sublayer (size 3.0) above it; value stayed 1.0,
  stack top stayed the root layer.
- CAUSE: A layer's own direct opinions always beat its sublayers.
  Overrides only win against opinions in weaker layers (lower sublayers,
  references, payloads).
- RECOVERY: S4 v2 holds the base in a weaker sublayer file; the override
  stacks above that. Win + revert both proven.
- PREVENTION: Never test overrides against same-layer direct opinions.

## L3: variantSet needs declaration AND `=` form (corrected by M2)
- FAILURE: S5 text-authored `variantSet` failed twice: `=` without
  declaration (set silently dropped), then no-`=` with declaration
  ("Expected }", layer unopenable).
- CAUSE: Both halves matter. NVIDIA's own URDF converter emits
  `append variantSets = "Physics"` plus `variantSet "Physics" = {...}`
  (see m2_out/m2_bot/m2_bot.usda). The no-`=` form is invalid Sdf text.
- RECOVERY: Declare the set and use the `=` form; or author with the
  UsdVariantSets API (AddVariantSet/AddVariant/GetVariantEditContext),
  which S5 verified green. Diagnose with `GetNames()` before referencing.
- PREVENTION: Parse warnings don't fail sends; always verify composed
  prims exist. Trust machine-emitted USDA over remembered grammar.

## L4: precedence is Direct > Sublayer > Reference (doc line corrected)
- FAILURE: X3 assumed "Sublayers < Reference" (per the composition
  skill's ordering line); live result: a root sublayer over (5.0) BEAT
  the reference value (1.0), stack top the sublayer file.
- CAUSE: The referring layer stack (root + its sublayers) outranks
  reference arcs. The doc line is wrong for this configuration.
- RECOVERY: X3 proves the full chain: direct 2.0 wins over everything;
  without direct, sublayer 5.0 wins over reference 1.0.
- PREVENTION: Teach Direct > Sublayer > Reference. Re-verify if the
  configuration changes (e.g. sublayers inside the referenced asset).

## L5: Attribute.Clear() leaves a root property-stack entry (open)
- FINDING: After Clear(), value fell through to the sublayer (5.0) but
  the root layer still headed the property stack with authored=True.
- CAUSE: Unresolved (suspect: emptied spec placeholder vs true removal).
- RECOVERY: X3 avoids removal mechanics (fresh prims per case).
- PREVENTION: Do not teach Clear()-as-removal until resolved; prefer
  RemoveProperty or case-per-prim.
