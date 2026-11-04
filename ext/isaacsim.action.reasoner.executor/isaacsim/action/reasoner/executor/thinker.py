"""Thinker client: plain-English task -> action lines for the executor.

Stdlib only on purpose: no omni/isaac imports, so this module can be
unit-tested with a plain python outside Isaac Sim, exactly like protocol.py.

Backends:
  * glimmer - POSTs to the Modal OpenAI-compatible endpoint
    (/v1/chat/completions) and extracts action lines from the reply.
  * mock    - deterministic keyword planner used when no endpoint is
    configured or the endpoint is unreachable. Lets the GUI flow and the
    executor be tested with no GPU.

Config: ext data/thinker_config.json, ~/.action_reasoner.json, or env vars
(GLIMMER_ENDPOINT, GLIMMER_API_KEY, GLIMMER_MODEL). Env vars win per-field.
"""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

MODEL_DEFAULT = "glimmer-30b"
ENV_ENDPOINT = "GLIMMER_ENDPOINT"
ENV_API_KEY = "GLIMMER_API_KEY"
ENV_MODEL = "GLIMMER_MODEL"
CONFIG_FILENAME = "thinker_config.json"
GUIDED_FILENAME = "guided_action_regex.txt"
MAX_IMAGES = 3
MAX_IMAGE_BYTES = 8 * 1024 * 1024

_ACTION_KEY_RE = re.compile(r"^[A-Za-z]\w*(\.\w+)+$")
_LIST_PREFIX_RE = re.compile(r"^\s*(?:\d+[.)]\s*|[-*]\s+)(.*)$")

_STOPWORDS = frozenset(
    "a an the and or to in on of for with is are be please make me my our "
    "it its this that these those then than so as at by from up down out "
    "over under do does did will would can could should have has had not no "
    "if else when what which who how why there here all any some more most "
    "into onto want need like just very really also too only also than then".split()
)


class ThinkerError(Exception):
    """Raised when the LLM backend cannot produce a plan."""


@dataclass
class ThinkerConfig:
    endpoint: str = ""
    api_key: str = ""
    model: str = MODEL_DEFAULT
    timeout: int = 120

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def describe(self) -> str:
        if not self.configured:
            return "mock (no endpoint configured)"
        host = re.sub(r"^https?://", "", self.endpoint).split("/")[0]
        return f"glimmer ({host}, model={self.model})"


@dataclass
class ThinkerPlan:
    actions_text: str
    notes: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    backend: str = "mock"
    raw: str = ""
    images: int = 0  # screenshot blocks actually sent to the endpoint


def default_config_paths() -> list:
    """Candidate config files: ext data dir, then home dir."""
    here = Path(__file__).resolve()
    paths = []
    if len(here.parents) >= 5:
        # .../isaacsim/action/reasoner/executor/thinker.py -> ext root/data/
        paths.append(here.parents[4] / "data" / CONFIG_FILENAME)
    try:
        paths.append(Path.home() / ".action_reasoner.json")
    except Exception:
        pass
    return paths


def _normalize_endpoint(endpoint: str) -> str:
    base = (endpoint or "").strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def load_config(explicit_path=None) -> ThinkerConfig:
    """Load config from file, with env vars overriding per-field."""
    data: dict = {}
    candidates = [Path(explicit_path)] if explicit_path else default_config_paths()
    for path in candidates:
        try:
            if path and path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                break
        except (OSError, ValueError):
            continue
    if not isinstance(data, dict):
        data = {}
    import os

    endpoint = os.environ.get(ENV_ENDPOINT, "") or str(data.get("endpoint") or "")
    api_key = os.environ.get(ENV_API_KEY, "") or str(data.get("api_key") or "")
    model = os.environ.get(ENV_MODEL, "") or str(data.get("model") or MODEL_DEFAULT)
    try:
        timeout = int(data.get("timeout", 120))
    except (TypeError, ValueError):
        timeout = 120
    return ThinkerConfig(
        endpoint=_normalize_endpoint(endpoint),
        api_key=api_key.strip(),
        model=model.strip() or MODEL_DEFAULT,
        timeout=timeout,
    )


def _tokens(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def select_skills(task: str, routing, top_k: int = 5) -> list:
    """Pick the most relevant skills by keyword overlap with the task."""
    task_words = _tokens(task)
    if not task_words or not routing:
        return []
    scored = []
    for entry in routing:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("skill") or entry.get("name") or "")
        desc = str(entry.get("description") or "")
        hay = _tokens(name.replace("-", " ") + " " + desc)
        overlap = task_words & hay
        if overlap:
            scored.append((len(overlap), name, entry))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [entry for _, _, entry in scored[: max(top_k, 0)]]


def build_system_prompt(action_signatures, skills, loop: bool = False) -> str:
    """System prompt: action-only output over the runnable actions.

    ``loop`` adds the multi-step Reasoner rules (DONE verdict, no
    repeats); single-shot Think keeps the original prompt untouched.
    """
    lines = [
        "You are the Action Reasoner Thinker inside NVIDIA Isaac Sim.",
        "Turn the user's task into simulator action lines for the executor.",
        "",
        "OUTPUT RULES (strict):",
        "- Output ONLY action lines, one per line: <action.key> k=v k=v ...",
        "- Values with commas have no spaces: pos=0,0,0.5",
        "- Lines starting with # are comments and allowed.",
        "- No prose, no numbering, no code fences, no explanations outside # comments.",
        "- Use ONLY the runnable actions listed below. Never invent action keys.",
        "- Targets are registry names (cube_01) or absolute paths (/World/x).",
        "- Bodies must never interpenetrate at spawn (keep a small gap);",
        "  overlapping bodies explode apart on sim.play.",
        "- If a screenshot is attached, use it to ground positions and to",
        "  check what already exists before creating (no duplicate planes).",
        "- Physics edits, joints and articulation need a paused timeline;",
        "  put sim.play last, only when the task wants motion.",
    ]
    if loop:
        lines += [
            "",
            "LOOP RULES (multi-step run; you get a fresh snapshot and",
            "screenshot every turn):",
            "- When the task is FULLY complete, reply with ONLY this line: DONE",
            "- Otherwise reply with ONLY the next action lines (repairs or",
            "  follow-ups for what is still missing or failed).",
            "- Never repeat actions that already succeeded; check the",
            "  snapshot first so you never duplicate prims.",
            "- DONE and the runnable actions below are all you may emit.",
        ]
    if action_signatures:
        lines += ["", "RUNNABLE ACTIONS:"] + [f"- {sig}" for sig in action_signatures]
    if skills:
        lines += _skill_docs_block(skills)
    return "\n".join(lines) + "\n"


def _skill_docs_block(skills) -> list:
    """RELEVANT SKILL DOCS lines, shared by plan and dispatch prompts."""
    block = ["", "RELEVANT SKILL DOCS (follow their guidance):"]
    for entry in skills:
        name = entry.get("skill") or entry.get("name") or "?"
        desc = (entry.get("description") or "")[: 220]
        extras = "/".join(
            x
            for x, flag in (
                ("scripts", entry.get("has_scripts")),
                ("refs", entry.get("has_references")),
            )
            if flag
        )
        suffix = f" [{extras}]" if extras else ""
        block.append(f"- {name}: {desc}{suffix}")
    return block


def build_dispatch_prompt(roster_lines, skills) -> str:
    """System prompt for dispatch mode: composite task -> deploy plan.

    ``roster_lines`` comes from dispatcher.describe_roster() (passed in
    so this module stays import-standalone for unit tests).
    """
    lines = [
        "You are the Action Reasoner Dispatcher inside NVIDIA Isaac Sim.",
        "Turn the user's composite task into a skill-agent deploy plan.",
        "",
        "OUTPUT RULES (strict):",
        "- Output ONLY dispatch lines, one per line.",
        "- DEPLOY agent=<name> [needs=<a+b+...>]",
        "- STEP n=<1..> agent=<name> do=<slug>",
        "- PARALLEL agents=<a+b+...> and COWORK agents=<a+b+...> group agents.",
        "- Lines starting with # are comments and allowed.",
        "- No prose, no numbering, no code fences.",
        "- Use ONLY the roster agents below. DEPLOY before first use.",
        "- STEP n starts at 1 and increases by 1 in block order.",
        "- More than one worker agent requires xval deployed.",
        "- Values carry no spaces; do= is a slug, not a sentence.",
        "",
        "ROSTER (agent -> skill pack):",
    ] + list(roster_lines)
    if skills:
        lines += _skill_docs_block(skills)
    return "\n".join(lines) + "\n"


def build_user_prompt(task: str, snapshot: str = "") -> str:
    parts = [f"TASK: {task.strip()}"]
    if snapshot and snapshot.strip():
        parts += ["", "LIVE STAGE SNAPSHOT (telemetry, ground truth):", snapshot.strip()]
    parts += ["", "Reply with action lines only."]
    return "\n".join(parts)


def encode_image(path) -> str:
    """Read a PNG file -> base64 data URL. Raises ThinkerError."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise ThinkerError(f"cannot read image {path}: {exc}")
    if len(data) > MAX_IMAGE_BYTES:
        raise ThinkerError(f"image too large ({len(data)} bytes): {path}")
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def build_user_content(task: str, snapshot: str = "", image_paths=()) -> tuple:
    """User message content: plain text, or OpenAI vision blocks + notes.

    Returns (content, notes, images_used). Unreadable images are skipped
    with a note; only the first MAX_IMAGES are sent.
    """
    text = build_user_prompt(task, snapshot)
    paths = [p for p in (image_paths or []) if p]
    notes = []
    if len(paths) > MAX_IMAGES:
        notes.append(f"using first {MAX_IMAGES} of {len(paths)} images")
    parts = [{"type": "text", "text": text}]
    for path in paths[:MAX_IMAGES]:
        try:
            url = encode_image(path)
        except ThinkerError as exc:
            notes.append(str(exc))
            continue
        parts.append({"type": "image_url", "image_url": {"url": url}})
    if len(parts) == 1:
        return text, notes, 0
    return parts, notes, len(parts) - 1


def load_guided_regex() -> str:
    """Read the guided-decoding pattern, or "" when the artifact is absent."""
    paths = default_config_paths()
    if not paths:
        return ""
    candidate = paths[0].parent / GUIDED_FILENAME
    try:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return ""


def _request_body(model: str, messages, max_tokens: int,
                  stream: bool = False, guided_regex=None) -> dict:
    """Chat-completions body; guided_regex only when provided (default-off)."""
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    if stream:
        body["stream"] = True
    if guided_regex:
        body["guided_regex"] = guided_regex
    return body


def chat_completion(endpoint: str, api_key: str, model: str, messages,
                    timeout: int = 120, max_tokens: int = 1024,
                    guided_regex=None) -> str:
    """Call an OpenAI-compatible /v1/chat/completions endpoint (stdlib)."""
    body = json.dumps(
        _request_body(model, messages, max_tokens,
                      guided_regex=guided_regex)).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[: 300]
        except Exception:
            detail = ""
        raise ThinkerError(f"endpoint HTTP {exc.code}: {detail or exc.reason}")
    except urllib.error.URLError as exc:
        raise ThinkerError(f"endpoint unreachable: {exc.reason}")
    except (ValueError, TimeoutError) as exc:
        raise ThinkerError(f"bad endpoint reply: {exc}")
    try:
        return payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise ThinkerError(f"unexpected reply shape: {str(payload)[:200]}")


def stream_completion(endpoint: str, api_key: str, model: str, messages,
                      timeout: int = 120, max_tokens: int = 1024,
                      guided_regex=None):
    """Yield content deltas from an SSE chat stream. Raises ThinkerError.

    Same OpenAI-compatible endpoint as chat_completion with
    ``"stream": True`` (vLLM serves SSE chunks + ``data: [DONE]``).
    Closing the generator early stops the read and the response.
    """
    body = json.dumps(
        _request_body(model, messages, max_tokens, stream=True,
                      guided_regex=guided_regex)).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[: 300]
        except Exception:
            detail = ""
        raise ThinkerError(f"endpoint HTTP {exc.code}: {detail or exc.reason}")
    except urllib.error.URLError as exc:
        raise ThinkerError(f"endpoint unreachable: {exc.reason}")
    with response:
        try:
            for raw in response:
                if isinstance(raw, bytes):
                    line = raw.decode("utf-8", "replace").strip()
                else:
                    line = raw.strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    payload = json.loads(data)
                except ValueError:
                    continue
                try:
                    delta = payload["choices"][0]["delta"].get("content") or ""
                except (KeyError, IndexError, TypeError, AttributeError):
                    continue
                if delta:
                    yield delta
        except urllib.error.HTTPError as exc:
            raise ThinkerError(f"stream broke: HTTP {exc.code}")
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                OSError) as exc:
            raise ThinkerError(f"stream broke: {exc}")


def _raw_verdict_done(raw: str) -> bool:
    """True when the raw reply carries a DONE verdict line.

    Checked pre-extraction in loop mode (the extractor would drop DONE
    as prose); window.py re-checks post-extraction via
    reasoner.split_verdict as the second layer.
    """
    for line in (raw or "").splitlines():
        stripped = _LIST_PREFIX_RE.sub(r"\1", line.strip()).strip()
        if stripped.upper() == "DONE":
            return True
    return False


def extract_actions(text: str, known_keys=None):
    """Split model output into (action_lines_text, dropped_prose_notes).

    Keeps # comments and dotted action keys; strips code fences and list
    markers; anything else is reported as dropped prose (capped).
    """
    known = set(known_keys or ())
    in_fence = False
    kept: list = []
    dropped: list = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not line:
            continue
        stripped = _LIST_PREFIX_RE.sub(r"\1", line).strip()
        if stripped.startswith("#"):
            kept.append(stripped)
            continue
        key = stripped.split(None, 1)[0] if stripped.split() else ""
        if _ACTION_KEY_RE.match(key) and (not known or key in known):
            kept.append(stripped)
        elif _ACTION_KEY_RE.match(key):
            kept.append("# DRAFT (not in catalog): " + stripped)
        else:
            dropped.append(line)
    notes = []
    if dropped:
        shown = dropped[:3]
        notes.append(f"dropped {len(dropped)} prose line(s): " + " | ".join(shown))
    return "\n".join(kept), notes


class StreamExtractor:
    """Incremental twin of extract_actions over a token stream.

    ``feed()`` takes raw text chunks and returns the complete kept lines
    as (is_comment, line) tuples; ``flush()`` processes the tail and
    returns (items, notes). ``feed(all) + flush()`` equals
    ``extract_actions(all)``. With ``verdict=True`` a DONE line sets
    ``done`` instead of dropping as prose (loop-mode verdicts).
    """

    def __init__(self, known_keys=None, verdict: bool = False):
        self.known = set(known_keys or ())
        self.verdict = verdict
        self.in_fence = False
        self.done = False
        self._buf = ""
        self._dropped: list = []

    def _process(self, raw_line: str):
        """One raw line -> (is_comment, line) or None. Mirrors batch."""
        line = raw_line.strip()
        if line.startswith("```"):
            self.in_fence = not self.in_fence
            return None
        if not line:
            return None
        stripped = _LIST_PREFIX_RE.sub(r"\1", line).strip()
        if self.verdict and stripped.upper() == "DONE":
            self.done = True
            return None
        if stripped.startswith("#"):
            return True, stripped
        key = stripped.split(None, 1)[0] if stripped.split() else ""
        if _ACTION_KEY_RE.match(key) and (not self.known or key in self.known):
            return False, stripped
        if _ACTION_KEY_RE.match(key):
            return True, "# DRAFT (not in catalog): " + stripped
        self._dropped.append(line)
        return None

    def feed(self, chunk: str) -> list:
        """Absorb a text chunk; return newly completed kept lines."""
        self._buf += chunk or ""
        items = []
        while "\n" in self._buf:
            raw_line, self._buf = self._buf.split("\n", 1)
            item = self._process(raw_line)
            if item is not None:
                items.append(item)
        return items

    def flush(self) -> tuple:
        """Process the tail; return (items, notes) like the batch form."""
        items = []
        if self._buf.strip():
            item = self._process(self._buf)
            if item is not None:
                items.append(item)
        self._buf = ""
        notes = []
        if self._dropped:
            shown = self._dropped[:3]
            notes.append(f"dropped {len(self._dropped)} prose line(s): "
                         + " | ".join(shown))
        return items, notes


def _has_plane(snapshot: str) -> bool:
    return "GroundPlane" in (snapshot or "")


# -- mock planner vocabulary: task -> parametric shape specs ---------------

_MOCK_PLANE_WORDS = {"plane", "ground", "floor", "scene"}
_MOCK_PLAY_WORDS = {"play", "run", "simulate", "simulation", "drive",
                    "move", "roll"}
_MOCK_LIDAR_WORDS = {"lidar", "sensor", "scan"}
_MOCK_MASS_WORDS = {"mass", "heavy", "heavier", "weight"}
_MOCK_TOWER_WORDS = {"tower", "towers", "stack", "stacks", "stacked"}

_MOCK_SHAPES = (
    ("create.objects.cuboid",
     {"cube", "cubes", "box", "boxes", "cuboid", "brick", "bricks",
      "block", "blocks"}),
    ("create.objects.sphere", {"sphere", "spheres", "ball", "balls"}),
    ("create.objects.cylinder", {"cylinder", "cylinders", "tube", "tubes"}),
    ("create.objects.cone", {"cone", "cones"}),
    ("create.objects.capsule", {"capsule", "capsules"}),
)
_MOCK_STEMS = {
    "create.objects.cuboid": "cube",
    "create.objects.sphere": "sphere",
    "create.objects.cylinder": "cylinder",
    "create.objects.cone": "cone",
    "create.objects.capsule": "capsule",
}

_MOCK_COLORS = {
    "red": (1.0, 0.0, 0.0),
    "green": (0.2, 0.8, 0.2),
    "blue": (0.2, 0.4, 0.9),
    "yellow": (1.0, 1.0, 0.0),
    "orange": (1.0, 0.55, 0.0),
    "purple": (0.6, 0.2, 0.8),
    "pink": (1.0, 0.4, 0.7),
    "cyan": (0.0, 0.9, 0.9),
    "white": (1.0, 1.0, 1.0),
    "black": (0.1, 0.1, 0.1),
    "gray": (0.5, 0.5, 0.5),
    "grey": (0.5, 0.5, 0.5),
    "brown": (0.5, 0.3, 0.1),
}
_MOCK_DEFAULT_COLORS = {"create.objects.cuboid": (0.2, 0.4, 0.9)}

_MOCK_SIZES = {"tiny": 0.5, "small": 0.7, "medium": 1.0, "big": 1.5,
               "large": 2.0, "huge": 2.5, "giant": 3.0}
_MOCK_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6}
_MOCK_COUNT_MAX = 6
_MOCK_CLAUSE_RE = re.compile(r"\b(?:and|then)\b|[,;+]")
_MOCK_ROW_GAP = 0.6
_MOCK_STACK_GAP = 0.1


def _mock_clause_spec(words: list):
    """Parse one clause -> shape spec dict, or None when no shape word.

    First shape word wins; the first count / color / size in the clause
    attach to it, so "red cube and blue sphere" pairs correctly.
    """
    key = None
    for word in words:
        for cand, vocab in _MOCK_SHAPES:
            if word in vocab:
                key = cand
                break
        if key is not None:
            break
    if key is None:
        return None
    count, color_name, size_name = 1, None, None
    count_seen = False
    for word in words:
        if not count_seen and word in _MOCK_NUMBERS:
            count, count_seen = _MOCK_NUMBERS[word], True
        elif not count_seen and word.isdigit():
            count, count_seen = int(word), True
        if color_name is None and word in _MOCK_COLORS:
            color_name = word
        if size_name is None and word in _MOCK_SIZES:
            size_name = word
    return {"key": key, "count": count, "color": color_name,
            "size": size_name,
            "factor": _MOCK_SIZES.get(size_name, 1.0),
            "heavy": False,
            "tower": bool(set(words) & _MOCK_TOWER_WORDS)}


def _mock_dims(key: str, factor: float) -> dict:
    if key == "create.objects.cuboid":
        return {"size": 1.0 * factor}
    if key == "create.objects.sphere":
        return {"radius": 0.4 * factor}
    if key == "create.objects.capsule":
        return {"radius": 0.3 * factor, "height": 1.0 * factor}
    return {"radius": 0.4 * factor, "height": 1.0 * factor}  # cyl + cone


def _mock_extents(key: str, dims: dict) -> tuple:
    """(horizontal width, vertical extent) for overlap-free layout."""
    if key == "create.objects.cuboid":
        return dims["size"], dims["size"]
    if key == "create.objects.sphere":
        return 2 * dims["radius"], 2 * dims["radius"]
    if key == "create.objects.capsule":
        return 2 * dims["radius"], dims["height"] + 2 * dims["radius"]
    return 2 * dims["radius"], dims["height"]  # cylinder + cone


def _mock_num(value) -> str:
    return "%g" % (float(value),)


def _mock_shape_line(key: str, pos, dims: dict, color, name) -> str:
    parts = [key]
    if name is not None:
        parts.append(f"name={name}")
    for param in ("size", "radius", "height"):
        if param in dims:
            parts.append(f"{param}={_mock_num(dims[param])}")
    parts.append("pos=" + ",".join(_mock_num(v) for v in pos))
    if color is not None:
        parts.append("color=" + ",".join(_mock_num(v) for v in color))
    return " ".join(parts)


def mock_plan(task: str, snapshot: str = "") -> tuple:
    """Deterministic task parser. Returns (actions_text, notes).

    Splits the task into clauses (on and/then/commas) and parses each
    into a shape spec: count (words or digits, capped), color, size
    adjective, tower stacking, and heavy/weight. Instances are laid out
    overlap-free (row, or one vertical stack per tower clause). Emits
    only handled actions; snapshot-aware (skips the ground plane when
    one already exists so the plan can run as-is).
    """
    words = _tokens(task or "")
    lines: list = []
    wants = []
    cap_notes: list = []

    def want_plane() -> bool:
        return not _has_plane(snapshot)

    if words & {"rover", "robot", "car", "moon", "wheels", "articulation"}:
        wants.append("rover")
        # Damping-only drives just add friction; drive/move/roll means the
        # user wants motion, so command a wheel speed (5 rad/s ~ 1.5 m/s).
        drive = bool(words & {"drive", "move", "roll"})
        if want_plane():
            lines.append("create.objects.plane size=20")
        # Wheels at ±0.95 clear the 0.6 half-width chassis by 0.05; ±0.75
        # interpenetrates it and PhysX ejects a wheel on play (seen live).
        vel = " target_velocity=5" if drive else ""
        lines += [
            "create.objects.cuboid name=chassis size=1.2 pos=0,0,0.65",
            "create.objects.sphere name=wheel_l radius=0.3 pos=0,0.95,0.3",
            "create.objects.sphere name=wheel_r radius=0.3 pos=0,-0.95,0.3",
            "joint.create.joint joint_type=revolute from_prim=chassis to_prim=wheel_l axis=Y",
            "joint.create.joint joint_type=revolute from_prim=chassis to_prim=wheel_r axis=Y",
            "robot.add.articulation path=chassis",
            "robot.set.joint_drive target=chassis_to_wheel_l stiffness=0 damping=500 max_force=100" + vel,
            "robot.set.joint_drive target=chassis_to_wheel_r stiffness=0 damping=500 max_force=100" + vel,
        ]
        if drive:
            wants.append("drive (target_velocity=5)")
        if words & {"lidar", "sensor", "scan"}:
            lines.append("sensor.create.rtx_lidar path=lidar_top tick_rate=10")
            wants.append("lidar")
    else:
        specs = []
        pending_heavy = False
        for chunk in _MOCK_CLAUSE_RE.split(task or ""):
            clause_words = re.findall(r"[a-z0-9]+", chunk.lower())
            spec = _mock_clause_spec(clause_words)
            has_mass = bool(set(clause_words) & _MOCK_MASS_WORDS)
            if spec is not None:
                if has_mass or pending_heavy:
                    spec["heavy"] = True
                pending_heavy = False
                specs.append(spec)
            elif has_mass:
                if specs:
                    specs[-1]["heavy"] = True
                else:
                    pending_heavy = True
        plane_asked = bool(words & _MOCK_PLANE_WORDS)
        lidar_asked = bool(words & _MOCK_LIDAR_WORDS)
        play_asked = bool(words & _MOCK_PLAY_WORDS)
        for spec in specs:
            if spec["count"] > _MOCK_COUNT_MAX:
                cap_notes.append(
                    f"count capped at {_MOCK_COUNT_MAX} "
                    f"(asked {spec['count']})")
                spec["count"] = _MOCK_COUNT_MAX
            elif spec["count"] < 1:
                spec["count"] = 1
        if (plane_asked or specs) and want_plane():
            lines.append("create.objects.plane size=20")
            wants.append("plane")
        used_names: set = set()
        heavy_targets: list = []
        cursor = 0.0
        for spec in specs:
            key = spec["key"]
            stem = _MOCK_STEMS[key]
            dims = _mock_dims(key, spec["factor"])
            width, vert = _mock_extents(key, dims)
            color = (_MOCK_COLORS[spec["color"]] if spec["color"]
                     else _MOCK_DEFAULT_COLORS.get(key))
            name = None
            if spec["heavy"]:
                base = f"heavy_{stem}"
                name, i = base, 2
                while name in used_names:
                    name = f"{base}_{i}"
                    i += 1
                used_names.add(name)
                heavy_targets.append(name)
            mods = ",".join(m for m in
                            (spec["color"], spec["size"],
                             "heavy" if spec["heavy"] else "") if m)
            desc = (f"{spec['count']}x {stem}" if spec["count"] > 1
                    else stem) + (f"({mods})" if mods else "")
            if spec["tower"] and spec["count"] > 1:
                x = cursor + width / 2
                for i in range(spec["count"]):
                    lines.append(_mock_shape_line(
                        key, (x, 0, 2.0 + i * (vert + _MOCK_STACK_GAP)),
                        dims, color, name if i == 0 else None))
                cursor += width + _MOCK_ROW_GAP
                wants.append("tower " + desc)
            else:
                for i in range(spec["count"]):
                    x = cursor + width / 2
                    lines.append(_mock_shape_line(
                        key, (x, 0, 2.0), dims, color,
                        name if i == 0 else None))
                    cursor += width + _MOCK_ROW_GAP
                wants.append(desc)
        if heavy_targets:
            for target in heavy_targets:
                lines.append(f"physics.set.mass target={target} value=5")
            wants.append("mass")
        if lidar_asked:
            lines.append("sensor.create.rtx_lidar path=lidar_top tick_rate=10")
            wants.append("lidar")
        if not lines and not play_asked:
            blocked = (plane_asked and not want_plane()) or (
                pending_heavy and not specs)
            if blocked:
                if pending_heavy and not specs:
                    cap_notes.append("weight/mass needs a shape in the task; "
                                     "no plan emitted")
            else:
                if want_plane():
                    lines.append("create.objects.plane size=20")
                lines += [
                    "create.objects.cuboid size=1 pos=0,0,2 color=0.2,0.4,0.9",
                    "create.objects.sphere radius=0.4 pos=1.5,0,2",
                ]
                wants.append("demo scene (no keywords matched)")
    if words & _MOCK_PLAY_WORDS:
        lines.append("sim.play")
        wants.append("play")

    notes = [
        "mock planner (no LLM): matched " +
        (", ".join(wants) if wants else "nothing actionable"),
        "tip: configure the Glimmer endpoint for free-form tasks",
    ] + cap_notes
    if _has_plane(snapshot):
        notes.append("snapshot already has a ground plane; plane line skipped")
    return "\n".join(lines), notes


def plan(task: str, snapshot: str = "", action_signatures=(), skills=(),
         known_keys=None, config: ThinkerConfig | None = None,
         images=(), loop: bool = False, guided_regex=None) -> ThinkerPlan:
    """Plan a task via Glimmer when configured, else via the mock planner.

    ``images`` is a list of screenshot paths; Glimmer is multimodal, so up
    to MAX_IMAGES are sent as vision blocks with the user message.
    ``loop`` switches the system prompt to the multi-step Reasoner rules.
    """
    cfg = config or load_config()
    skill_names = [str(s.get("skill") or s.get("name")) for s in (skills or [])]
    if not cfg.configured:
        actions_text, notes = mock_plan(task, snapshot)
        notes = [
            "endpoint not configured (set GLIMMER_ENDPOINT + GLIMMER_API_KEY "
            "or write thinker_config.json); using mock planner"
        ] + notes
        if images:
            notes.append(f"{len(images)} image(s) attached; mock planner is text-only")
        return ThinkerPlan(actions_text=actions_text, notes=notes,
                           skills=skill_names, backend="mock")
    system = build_system_prompt(list(action_signatures), list(skills or []),
                                 loop=loop)
    content, img_notes, images_used = build_user_content(task, snapshot, images)
    try:
        raw = chat_completion(cfg.endpoint, cfg.api_key, cfg.model, [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ], timeout=cfg.timeout, guided_regex=guided_regex)
    except ThinkerError as exc:
        actions_text, mock_notes = mock_plan(task, snapshot)
        notes = [f"endpoint failed ({exc}); fell back to mock planner"] + mock_notes
        return ThinkerPlan(actions_text=actions_text, notes=notes,
                           skills=skill_names, backend="mock")
    if loop and _raw_verdict_done(raw):
        return ThinkerPlan(actions_text="DONE\n",
                           notes=img_notes + ["planner verdict DONE"],
                           skills=skill_names, backend="glimmer", raw=raw,
                           images=images_used)
    actions_text, notes = extract_actions(raw, known_keys)
    notes = img_notes + notes
    if not actions_text.strip():
        fallback, mock_notes = mock_plan(task, snapshot)
        notes = ["endpoint returned no action lines; fell back to mock planner",
                 f"raw reply kept ({len(raw)} chars)"] + mock_notes
        return ThinkerPlan(actions_text=fallback, notes=notes,
                           skills=skill_names, backend="mock", raw=raw)
    return ThinkerPlan(actions_text=actions_text, notes=notes,
                       skills=skill_names, backend="glimmer", raw=raw,
                       images=images_used)


def plan_stream(task: str, snapshot: str = "", action_signatures=(),
                skills=(), known_keys=None, config: ThinkerConfig | None = None,
                images=(), loop: bool = False, on_line=None,
                guided_regex=None) -> ThinkerPlan:
    """Plan with live line delivery: on_line(line, is_comment) -> bool.

    Each complete action/comment line is delivered the moment it finishes
    streaming, so the caller can trigger it instantly instead of waiting
    for the full reply. The sink returns False to stop the stream early.
    Fallbacks mirror plan(): unconfigured/failed/empty answers emit mock
    lines through the same sink. A break AFTER lines landed keeps the
    partial plan (no mock fallback mid-run: triggered lines must not
    repeat). The tail of a broken stream is dropped, never flushed: it is
    known-incomplete, unlike batch end-of-text.
    """
    cfg = config or load_config()
    skill_names = [str(s.get("skill") or s.get("name")) for s in (skills or [])]
    sink = on_line or (lambda line, is_comment: True)

    def _emit_mock(reason_note: str) -> ThinkerPlan:
        actions_text, mock_notes = mock_plan(task, snapshot)
        delivered = []
        for raw_line in actions_text.splitlines():
            if not raw_line.strip():
                continue
            if not sink(raw_line, raw_line.startswith("#")):
                break
            delivered.append(raw_line)
        notes = [reason_note] + mock_notes
        if images:
            notes.append(f"{len(images)} image(s) attached; "
                         "mock planner is text-only")
        return ThinkerPlan(actions_text="\n".join(delivered), notes=notes,
                           skills=skill_names, backend="mock")

    if not cfg.configured:
        return _emit_mock(
            "endpoint not configured (set GLIMMER_ENDPOINT + GLIMMER_API_KEY "
            "or write thinker_config.json); using mock planner")
    system = build_system_prompt(list(action_signatures), list(skills or []),
                                 loop=loop)
    content, img_notes, images_used = build_user_content(task, snapshot, images)
    extractor = StreamExtractor(known_keys, verdict=loop)
    delivered: list = []
    raw_parts: list = []
    stopped = False
    broke = None
    gen = stream_completion(cfg.endpoint, cfg.api_key, cfg.model, [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ], timeout=cfg.timeout, guided_regex=guided_regex)
    try:
        for delta in gen:
            raw_parts.append(delta)
            for is_comment, line in extractor.feed(delta):
                delivered.append(line)
                if not sink(line, is_comment):
                    stopped = True
                    break
            if stopped or (loop and extractor.done):
                break
    except ThinkerError as exc:
        broke = exc
    finally:
        gen.close()
    raw = "".join(raw_parts)
    if broke is not None and delivered:
        notes = img_notes + [f"stream broke ({broke}); kept {len(delivered)} "
                             "line(s)"]
        return ThinkerPlan(actions_text="\n".join(delivered), notes=notes,
                           skills=skill_names, backend="glimmer", raw=raw,
                           images=images_used)
    if broke is not None:
        return _emit_mock(f"endpoint failed ({broke}); "
                          "fell back to mock planner")
    if loop and extractor.done:
        return ThinkerPlan(actions_text="DONE\n",
                           notes=img_notes + ["planner verdict DONE"],
                           skills=skill_names, backend="glimmer", raw=raw,
                           images=images_used)
    tail, drop_notes = extractor.flush()
    if not stopped:
        for is_comment, line in tail:
            delivered.append(line)
            if not sink(line, is_comment):
                break
    notes = img_notes + drop_notes
    if not delivered:
        plan = _emit_mock("endpoint returned no action lines; "
                          "fell back to mock planner")
        plan.notes.insert(1, f"raw reply kept ({len(raw)} chars)")
        plan.raw = raw
        return plan
    return ThinkerPlan(actions_text="\n".join(delivered), notes=notes,
                       skills=skill_names, backend="glimmer", raw=raw,
                       images=images_used)


def _strip_fences(text: str) -> str:
    """Drop ``` fence lines; dispatch validation stays strict after that."""
    kept = [ln for ln in (text or "").splitlines()
            if not ln.strip().startswith("```")]
    out = "\n".join(kept)
    return out + "\n" if out and not out.endswith("\n") else out


def plan_dispatch(task: str, snapshot: str = "", roster_lines=(),
                  skills=(), config: ThinkerConfig | None = None,
                  images=(), guided_regex=None, validate=None) -> ThinkerPlan:
    """Dispatch a composite task: deploy plan via Glimmer.

    ``roster_lines`` comes from dispatcher.describe_roster() and
    ``validate`` is dispatcher.validate_block (both injected so this
    module stays import-standalone for unit tests). There is no mock
    fallback: a guessed deploy plan is worse than none, so
    unconfigured/failed calls return an empty plan with notes.
    """
    cfg = config or load_config()
    skill_names = [str(s.get("skill") or s.get("name")) for s in (skills or [])]
    if not cfg.configured:
        notes = ["endpoint not configured (set GLIMMER_ENDPOINT + "
                 "GLIMMER_API_KEY or write thinker_config.json); "
                 "dispatch needs Glimmer (no mock deploy plans)"]
        if images:
            notes.append(f"{len(images)} image(s) attached; no plan emitted")
        return ThinkerPlan(actions_text="", notes=notes,
                           skills=skill_names, backend="mock")
    system = build_dispatch_prompt(list(roster_lines), list(skills or []))
    content, img_notes, images_used = build_user_content(task, snapshot, images)
    try:
        raw = chat_completion(cfg.endpoint, cfg.api_key, cfg.model, [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ], timeout=cfg.timeout, guided_regex=guided_regex)
    except ThinkerError as exc:
        return ThinkerPlan(actions_text="", notes=[f"endpoint failed ({exc}); "
                                                  "no deploy plan"],
                           skills=skill_names, backend="mock")
    cleaned = _strip_fences(raw)
    if not cleaned.strip():
        return ThinkerPlan(actions_text="", notes=img_notes + [
            "endpoint returned no dispatch lines; no deploy plan"],
            skills=skill_names, backend="glimmer", raw=raw,
            images=images_used)
    if validate is not None:
        try:
            validate(cleaned)
        except Exception as exc:
            return ThinkerPlan(actions_text="", notes=img_notes + [
                f"dispatch invalid ({exc}); no deploy plan"],
                skills=skill_names, backend="glimmer", raw=raw,
                images=images_used)
    return ThinkerPlan(actions_text=cleaned, notes=img_notes,
                       skills=skill_names, backend="glimmer", raw=raw,
                       images=images_used)
