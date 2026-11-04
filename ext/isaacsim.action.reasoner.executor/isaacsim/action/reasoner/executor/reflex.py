"""Reflex dispatcher: millisecond NL -> action lines, no LLM call.

Stdlib only on purpose: no omni/isaac imports, so this module can be
unit-tested with a plain python outside Isaac Sim, exactly like
protocol.py, thinker.py, and reasoner.py.

``try_reflex()`` matches ONLY primitive single-intent commands (create
one kind of shape, sim transport, delete a named prim). Anything
compositional returns None so the Thinker (Glimmer, else mock) plans it.

Deliberately not built on thinker.mock_plan: the mock planner never
returns None and emits a demo scene when nothing matches, which is the
right fallback contract but the wrong dispatcher contract.
"""
from __future__ import annotations

import re

# action key, trigger words, catalog-default dims (scaled by size words)
_SHAPES = (
    ("create.objects.cuboid",
     {"cube", "cubes", "cuboid", "box", "boxes", "brick", "bricks",
      "block", "blocks"},
     {"size": 1.0}),
    ("create.objects.sphere", {"sphere", "spheres", "ball", "balls"},
     {"radius": 0.5}),
    ("create.objects.cylinder",
     {"cylinder", "cylinders", "tube", "tubes"},
     {"radius": 0.4, "height": 1.0}),
    ("create.objects.cone", {"cone", "cones"},
     {"radius": 0.4, "height": 1.0}),
    ("create.objects.capsule", {"capsule", "capsules"},
     {"radius": 0.3, "height": 1.0}),
)
_STEMS = {
    "create.objects.cuboid": "cuboid",
    "create.objects.sphere": "sphere",
    "create.objects.cylinder": "cylinder",
    "create.objects.cone": "cone",
    "create.objects.capsule": "capsule",
}
_SHAPE_WORDS = frozenset(w for _, vocab, _ in _SHAPES for w in vocab)

_CREATE_VERBS = frozenset(
    {"create", "make", "add", "spawn", "put", "place", "give", "build"})

_COLORS = {
    "red": (1.0, 0.0, 0.0), "green": (0.2, 0.8, 0.2),
    "blue": (0.2, 0.4, 0.9), "yellow": (1.0, 1.0, 0.0),
    "orange": (1.0, 0.55, 0.0), "purple": (0.6, 0.2, 0.8),
    "pink": (1.0, 0.4, 0.7), "cyan": (0.0, 0.9, 0.9),
    "white": (1.0, 1.0, 1.0), "black": (0.1, 0.1, 0.1),
    "gray": (0.5, 0.5, 0.5), "grey": (0.5, 0.5, 0.5),
    "brown": (0.5, 0.3, 0.1),
}
_SIZES = {"tiny": 0.5, "small": 0.7, "medium": 1.0, "big": 1.5,
          "large": 2.0, "huge": 2.5, "giant": 3.0}
_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
            "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
            "nineteen": 19, "twenty": 20}
_COUNT_MAX = 6

_PLAY_WORDS = frozenset({"play", "run", "simulate", "simulation"})
_TRANSPORT = (
    ("sim.play", frozenset({"play", "run", "simulate", "simulation"})),
    ("sim.pause", frozenset({"pause"})),
    ("sim.stop", frozenset({"stop"})),
    ("sim.reset", frozenset({"reset"})),
)
_TRANSPORT_WORDS = frozenset(w for _, vocab in _TRANSPORT for w in vocab)

_DELETE_VERBS = frozenset({"delete", "remove"})
_DROP_WORDS = frozenset(
    {"the", "a", "an", "that", "this", "those", "these", "it", "them",
     "my", "please", "plane", "ground", "floor", "object", "prim",
     "shape", "sim", "hundred", "thousand"}
    | _DELETE_VERBS | _CREATE_VERBS | _SHAPE_WORDS
    | set(_COLORS) | set(_SIZES))

# Compositional intents reflex must never grab (attach/joint/motion/mass/
# sensing/stacking all need multi-action planning by the Thinker).
_VETO = frozenset(
    {"attach", "attached", "joint", "joints", "drive", "driving",
     "move", "moving", "roll", "rolling", "rover", "robot", "lidar",
     "radar", "sensor", "scan", "mass", "heavy", "heavier", "weight",
     "stack", "stacked", "tower", "towers", "undo", "articulation",
     "gravity", "hundred", "thousand"})

_CLAUSE_RE = re.compile(r"\b(?:and|then)\b|[,;+]")
_PATH_RE = re.compile(r"/[\w/.-]+")
_ROW_GAP = 0.6
_SPAWN_Z = 2.0


def _has_plane(snapshot: str) -> bool:
    return "GroundPlane" in (snapshot or "")


def _num(value) -> str:
    return "%g" % (float(value),)


def _extents(key: str, dims: dict) -> tuple:
    """(horizontal width, vertical extent) for overlap-free layout."""
    if key == "create.objects.cuboid":
        return dims["size"], dims["size"]
    if key == "create.objects.sphere":
        return 2 * dims["radius"], 2 * dims["radius"]
    if key == "create.objects.capsule":
        return 2 * dims["radius"], dims["height"] + 2 * dims["radius"]
    return 2 * dims["radius"], dims["height"]  # cylinder + cone


def _try_delete(task: str, words: set) -> tuple | None:
    if not (words & _DELETE_VERBS):
        return None
    if words & (_SHAPE_WORDS | _CREATE_VERBS | _TRANSPORT_WORDS):
        return None  # multi-intent ("delete X and create Y") -> Thinker
    paths = _PATH_RE.findall(task or "")
    if len(paths) > 1:
        return None
    if paths:
        target = paths[0]
    else:
        survivors = [w for w in re.findall(r"[a-z0-9_]+", task.lower())
                     if w not in _DROP_WORDS]
        if len(survivors) != 1 or not re.search(r"[0-9_]", survivors[0]):
            return None  # vague ("the cube") or destructive -> Thinker
        target = survivors[0]
    line = f"scene.delete.prim target={target}"
    return line, [f"reflex planner (no LLM call): matched delete {target}"]


def _try_shape(task: str, words: set, snapshot: str) -> tuple | None:
    if not (words & _SHAPE_WORDS):
        return None
    chunks = [c for c in _CLAUSE_RE.split(task or "") if c.strip()]
    shaped = []
    for chunk in chunks:
        chunk_words = re.findall(r"[a-z0-9]+", chunk.lower())
        found = {key for key, vocab, _ in _SHAPES
                 if set(chunk_words) & vocab}
        if found:
            shaped.append((chunk_words, found))
    if len(shaped) != 1:
        return None  # zero (unreachable) or multi-clause shapes -> Thinker
    chunk_words, found = shaped[0]
    if len(found) != 1:
        return None  # two shape kinds ("cube and sphere") -> Thinker
    key = next(iter(found))
    if not (set(chunk_words) & _CREATE_VERBS):
        return None  # no creation verb ("cube?") -> Thinker
    if words & (_DELETE_VERBS | (_TRANSPORT_WORDS - _PLAY_WORDS)):
        return None  # conflicting intent -> Thinker
    count, color_name, size_name = 1, None, None
    count_seen = False
    for word in chunk_words:
        if not count_seen and word in _NUMBERS:
            count, count_seen = _NUMBERS[word], True
        elif not count_seen and word.isdigit():
            count, count_seen = int(word), True
        if color_name is None and word in _COLORS:
            color_name = word
        if size_name is None and word in _SIZES:
            size_name = word
    if count < 1:
        count = 1
    notes: list = []
    if count > _COUNT_MAX:
        notes.append(f"count capped at {_COUNT_MAX} (asked {count})")
        count = _COUNT_MAX
    factor = _SIZES.get(size_name, 1.0)
    _, _, defaults = next(spec for spec in _SHAPES if spec[0] == key)
    dims = {param: default * factor for param, default in defaults.items()}
    width, _ = _extents(key, dims)
    color = _COLORS.get(color_name) if color_name else None
    lines: list = []
    if not _has_plane(snapshot):
        lines.append("create.objects.plane size=20")
    cursor = 0.0
    for _ in range(count):
        parts = [key]
        if factor != 1.0:
            for param in ("size", "radius", "height"):
                if param in dims:
                    parts.append(f"{param}={_num(dims[param])}")
        x = cursor + width / 2
        parts.append("pos=" + ",".join(_num(v) for v in (x, 0, _SPAWN_Z)))
        if color is not None:
            parts.append("color=" + ",".join(_num(v) for v in color))
        lines.append(" ".join(parts))
        cursor += width + _ROW_GAP
    if words & _PLAY_WORDS:
        lines.append("sim.play")
    mods = ",".join(m for m in (color_name, size_name) if m)
    stem = _STEMS[key]
    desc = (f"{count}x {stem}" if count > 1 else stem) + (
        f"({mods})" if mods else "")
    notes.insert(0, f"reflex planner (no LLM call): matched {desc}")
    return "\n".join(lines), notes


def _try_transport(words: set) -> tuple | None:
    if not (words & _TRANSPORT_WORDS):
        return None
    if words & (_DELETE_VERBS | _CREATE_VERBS):
        return None  # conflicting intent -> Thinker
    kinds = [key for key, vocab in _TRANSPORT if words & vocab]
    if len(kinds) != 1:
        return None  # zero (unreachable) or mixed ("play then pause")
    return kinds[0], [f"reflex planner (no LLM call): matched {kinds[0]}"]


def try_reflex(task: str, snapshot: str = "") -> tuple | None:
    """Fast-path dispatch: (actions_text, notes), or None to use the Thinker.

    Fires only on primitive single-intent commands. Every other task —
    questions, multi-step builds, motion, sensing — falls through to
    Glimmer (or the mock planner when unconfigured).
    """
    if not (task or "").strip():
        return None
    # Keep underscores so registry names (cube_01) never read as shape words.
    words = set(re.findall(r"[a-z0-9_]+", task.lower()))
    if words & _VETO:
        return None
    if words & _SHAPE_WORDS:
        return _try_shape(task, words, snapshot)
    if words & _DELETE_VERBS:
        return _try_delete(task, words)
    return _try_transport(words)
