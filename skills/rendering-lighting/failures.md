# Rendering & Lighting — Failure Catalog (live-verified)

## R5: DistantLight 3x swings move the mean only ~7% (OPEN)
- FAILURE: Sun 1500->4500 (dome 400, 100, and 0) moved mean
  143.6->146.2, 110.1->116.2, 94.8->101.3. Identical via during-play
  sets AND stop/set/play re-parse (so sets apply; the sun just
  contributes little to this view).
- CAUSE: Unknown. Candidates: sun direction lights unseen faces;
  hidden ambient floor (~95pts with dome=0 needs explaining).
  RULED OUT: tonemap compression (R4: filmIso 4x -> 1.49x pixels).
- RECOVERY: R3 drills the DOME lever instead (100->400: ratio 1.30).
- PREVENTION: Prove each light's leverage with a ratio gate before
  building drills on it. Discriminator for later: both-lights-to-0
  (black = sun is the floor; bright = hidden ambient).

## R4: get_data returns a per-camera LIST of warp arrays
- FAILURE: `np.asarray(sensor.get_data("rgb"))` died with
  "Invalid indexing in slice: 240" (numpy iterates __getitem__).
- CAUSE: Return is [wp.array(H,W,3)], not one array; warp raises
  RuntimeError (not IndexError) out-of-bounds, killing iteration.
- RECOVERY: Unwrap [0], then Skill 5 R2 rule (.numpy() conversion).
- PREVENTION: Always unwrap + convert warp sensor data explicitly.

## R3: installed 6.0.0 RtxCamera API differs from skill sketch
- FAILURE: `aux_output_level` kwarg rejected (TypeError);
  `resolution=(240,320)` tuple crashed broadcast_to ("Invalid
  indexing in slice: 240").
- CAUSE: Installed signatures lag/lead the skill examples.
- RECOVERY: Bare constructor + pose kwargs; resolution as LIST
  [240, 320]. Inspected live via inspect.signature/getsource.
- PREVENTION: Probe installed signatures before trusting examples.

## R2: USD camera matrix must be row-major (transpose numpy look-at)
- FAILURE: Camera authored from a numpy look-at (basis columns, eye
  in column 3) read back campos=[0,0,0]; camera faced wrong way.
- CAUSE: USD Gf.Matrix4d is row-major: basis vectors are ROWS 0-2,
  eye is ROW 3. Column-vector numpy math must be transposed.
- RECOVERY: `Gf.Matrix4d(*[float(v) for row in mat.T for v in row])`.
- PREVENTION: Always transpose column-vector look-at output for USD.

## R1: Gf.Matrix4d takes 16 scalars, not one tuple
- FAILURE: `Gf.Matrix4d(tuple-of-16)` raised TypeError (no converter
  to vector<double>).
- RECOVERY: Unpack: `Gf.Matrix4d(*vals)`.
- PREVENTION: Use the 16-scalar constructor form.
