"""Action protocol: parse + validate action lines.

Stdlib only on purpose: no omni/isaac imports, so this module can be
unit-tested with a plain python outside Isaac Sim.

Line format (one action per line, `#` starts a comment)::

    create.objects.cuboid size=1 pos=0,0,0.5 color=0.2,0.4,0.9
    joint.create.joint joint_type=revolute from_prim=chassis to_prim=wheel_fl axis=Y
    robot.add.articulation path=chassis
    sim.play
"""
from __future__ import annotations

import copy
import difflib
import json
import shlex
from dataclasses import dataclass, field


class ProtocolError(Exception):
    """Raised when a line cannot be parsed."""


class ValidationError(Exception):
    """Raised when an action fails validation. Carries all errors."""

    def __init__(self, errors: list):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


@dataclass
class ValidatedAction:
    key: str
    params: dict
    warnings: list = field(default_factory=list)


_TRUE = {"true", "1", "yes", "on"}
_FALSE = {"false", "0", "no", "off"}

# Catalog params that are runtime handles, never prompt input. They are
# exempt from "required" checks and injected as None; handlers fill them in.
AUTO_PARAMS = {"stage", "usd_context_name", "context_name", "viewport_api"}

# Prompt-friendly params not present in the catalog entry. Kept minimal and
# documented; each has a catalog-style {type, default} spec.
#
# Every shape creator also inherits the full rigid transform (orient, scale)
# below, so 3D models can be posed at spawn. The ground plane is excluded:
# tilting or rescaling the world floor is never what a prompt wants.
CREATE_EXTRA_SPECS = {
    "orient": {"type": "vec4", "default": None},  # quat x,y,z,w (set.pose order)
    "scale": {"type": "vec3", "default": None},
}
CREATE_NO_TRANSFORM = {"create.objects.plane"}

EXTRA_PARAM_SPECS = {
    "joint.create.joint": {
        "axis": {"type": "str", "default": "Z"},
        "name": {"type": "str", "default": None},
    },
    "sensor.create.rtx_lidar": {
        "path": {"type": "str", "default": None},
        "tick_rate": {"type": "float", "default": None},
        "config": {"type": "str", "default": None},
        "pos": {"type": "vec3", "default": None},
    },
    "sensor.create.rtx_radar": {
        "tick_rate": {"type": "float", "default": None},
    },
    "sensor.create.rtx_ultrasonic": {
        "tick_rate": {"type": "float", "default": None},
    },
    "robot.set.joint_drive": {
        "target_velocity": {"type": "float", "default": None},
        "target_position": {"type": "float", "default": None},
    },
}

JOINT_TYPES = ("fixed", "revolute", "prismatic", "spherical", "distance")


def load_catalog(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def effective_params(key: str, spec: dict) -> dict:
    """Catalog params merged with EXTRA_PARAM_SPECS for one action."""
    merged = dict(spec.get("params") or {})
    if key.startswith("create.") and key not in CREATE_NO_TRANSFORM:
        for name, espec in CREATE_EXTRA_SPECS.items():
            merged.setdefault(name, espec)
    for name, espec in EXTRA_PARAM_SPECS.get(key, {}).items():
        merged.setdefault(name, espec)
    return merged


def _base_type(type_name: str) -> str:
    return (type_name or "str").split("|")[0].strip().lower()


def coerce(type_name: str, raw: str, param: str):
    """Coerce one raw string value to its catalog type. Raises ValueError."""
    t = _base_type(type_name)
    text = raw.strip()
    if t in ("str", "name"):
        return text
    if t == "bool":
        low = text.lower()
        if low in _TRUE:
            return True
        if low in _FALSE:
            return False
        raise ValueError(f"param '{param}' wants bool, got '{raw}'")
    if t == "int":
        try:
            return int(text, 10)
        except ValueError:
            raise ValueError(f"param '{param}' wants int, got '{raw}'")
    if t == "float":
        try:
            return float(text)
        except ValueError:
            raise ValueError(f"param '{param}' wants float, got '{raw}'")
    if t in ("vec3", "vec4"):
        want = 3 if t == "vec3" else 4
        body = text.strip()
        if body.startswith("(") and body.endswith(")"):
            body = body[1:-1]
        parts = [p.strip() for p in body.split(",")]
        if len(parts) != want or any(p == "" for p in parts):
            raise ValueError(f"param '{param}' wants {want} comma values, got '{raw}'")
        try:
            return [float(p) for p in parts]
        except ValueError:
            raise ValueError(f"param '{param}' wants numbers, got '{raw}'")
    # Unknown catalog type: pass the string through, handler decides.
    return text


def parse_line(line: str, lineno: int = 0):
    """Parse one line -> (action_key, raw_params) or None for blank/comment.

    Backslashes are normalized to forward slashes BEFORE tokenizing:
    POSIX shlex would otherwise strip them (``C:\\stage\\x.usd`` arrived
    as ``C:stagex.usd``). No value in the action grammar needs a
    backslash; USD paths and Windows file APIs both accept ``/``.
    """
    text = line.strip().replace("\\", "/")
    if not text or text.startswith("#"):
        return None
    try:
        tokens = shlex.split(text, comments=True, posix=True)
    except ValueError as exc:
        raise ProtocolError(f"line {lineno}: cannot parse: {exc}")
    if not tokens:
        return None
    key = tokens[0]
    raw = {}
    for tok in tokens[1:]:
        if "=" not in tok:
            raise ProtocolError(f"line {lineno}: bad token '{tok}' (want key=value)")
        name, value = tok.split("=", 1)
        name = name.strip()
        if not name:
            raise ProtocolError(f"line {lineno}: bad token '{tok}' (want key=value)")
        raw[name] = value.strip()
    return key, raw


def parse_batch(text: str) -> list:
    """Parse a multi-line prompt -> [(key, raw_params, lineno)]."""
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        parsed = parse_line(line, lineno=i)
        if parsed is not None:
            key, raw = parsed
            out.append((key, raw, i))
    return out


def _vertical_scale(typed: dict) -> float:
    """Z scale multiplier for spawn-height clamps (1.0 when unscaled)."""
    scale = typed.get("scale")
    if isinstance(scale, list) and len(scale) == 3 and scale[2] > 0:
        return scale[2]
    return 1.0


def _clamp_rest(typed: dict, warnings: list, lineno: int,
                rest: float, label: str) -> None:
    pos = typed.get("pos")
    if isinstance(pos, list) and len(pos) == 3 and pos[2] < rest:
        pos[2] = rest
        warnings.append(f"line {lineno}: clamped pos.z to {label} ({rest})")


def _apply_offline_rules(key: str, typed: dict, warnings: list, errors: list, lineno: int) -> None:
    """Evaluate the catalog pre_rules that need no live stage."""
    if key == "create.objects.cuboid":
        size = typed.get("size") or 1.0
        _clamp_rest(typed, warnings, lineno,
                    size * _vertical_scale(typed) / 2, "size/2")
    elif key == "create.objects.sphere":
        radius = typed.get("radius") or 0.5
        _clamp_rest(typed, warnings, lineno,
                    radius * _vertical_scale(typed), "radius")
    elif key in (
        "create.objects.cylinder", "create.objects.cone",
        "create.objects.fixed_cylinder", "create.objects.fixed_cone",
        "create.objects.visual_cylinder", "create.objects.visual_cone",
    ):
        rest = (typed.get("height") or 1.0) * _vertical_scale(typed) / 2.0
        _clamp_rest(typed, warnings, lineno, rest, "height/2")
    elif key in (
        "create.objects.capsule",
        "create.objects.fixed_capsule",
        "create.objects.visual_capsule",
    ):
        rest = max((typed.get("height") or 1.0) / 2.0,
                   typed.get("radius") or 0.3) * _vertical_scale(typed)
        _clamp_rest(typed, warnings, lineno, rest, "rest height")
    elif key in ("create.objects.fixed_cuboid", "create.objects.visual_cuboid"):
        size = typed.get("size") or 1.0
        _clamp_rest(typed, warnings, lineno,
                    size * _vertical_scale(typed) / 2, "size/2")
    elif key in ("create.objects.fixed_sphere", "create.objects.visual_sphere"):
        radius = typed.get("radius") or 0.5
        _clamp_rest(typed, warnings, lineno,
                    radius * _vertical_scale(typed), "radius")
    elif key == "robot.set.velocity_limit":
        if (typed.get("value") or 0) <= 0:
            errors.append(f"line {lineno}: param 'value' must be > 0")
    elif key == "robot.clone":
        count = typed.get("count")
        if count is None or count < 1:
            errors.append(f"line {lineno}: param 'count' must be >= 1")
        elif count > 20:
            errors.append(f"line {lineno}: param 'count' capped at 20")
    elif key == "physics.set.mass":
        if (typed.get("value") or 0) <= 0:
            errors.append(f"line {lineno}: param 'value' must be > 0")
    elif key == "sim.step":
        if (typed.get("n") or 0) < 1:
            errors.append(f"line {lineno}: param 'n' must be >= 1")
    elif key == "scene.delete.prim":
        target = typed.get("target")
        if isinstance(target, str) and target.rstrip("/").rsplit("/", 1)[-1] == "PhysicsScene":
            errors.append(
                f"line {lineno}: refusing to delete the PhysicsScene "
                f"(orphans the physics backend; use scene.open to switch stages)"
            )
    elif key == "joint.create.joint":
        raw_type = typed.get("joint_type")
        norm = raw_type.strip().lower() if isinstance(raw_type, str) else ""
        if norm not in JOINT_TYPES:
            errors.append(
                f"line {lineno}: joint_type must be one of "
                f"{'/'.join(JOINT_TYPES)}, got '{raw_type}'"
            )
        else:
            typed["joint_type"] = norm
        axis = typed.get("axis")
        if isinstance(axis, str):
            axis = axis.strip().upper()
            if axis not in ("X", "Y", "Z"):
                errors.append(f"line {lineno}: axis must be X, Y or Z, got '{typed.get('axis')}'")
            else:
                typed["axis"] = axis


def validate(key: str, raw: dict, catalog: dict, lineno: int = 0) -> ValidatedAction:
    """Validate raw params against the catalog. Injects defaults."""
    spec = catalog.get(key)
    if spec is None:
        tips = difflib.get_close_matches(key, catalog.keys(), n=3, cutoff=0.55)
        hint = f" (did you mean: {', '.join(tips)}?)" if tips else ""
        raise ValidationError([f"line {lineno}: unknown action '{key}'{hint}"])
    if not spec.get("available", True):
        raise ValidationError(
            [f"line {lineno}: action '{key}' is unavailable ({spec.get('resolution')})"]
        )
    params_spec = effective_params(key, spec)
    allow_extra = {"name"} if key.startswith("create.") else set()
    errors = []
    warnings = []
    for name in raw:
        if name not in params_spec and name not in allow_extra:
            errors.append(f"line {lineno}: unknown param '{name}' for '{key}'")
    typed = {}
    for pname, pspec in params_spec.items():
        pspec = pspec if isinstance(pspec, dict) else {}
        if pname in raw:
            try:
                typed[pname] = coerce(pspec.get("type", "str"), raw[pname], pname)
            except ValueError as exc:
                errors.append(f"line {lineno}: {exc}")
        elif pname in AUTO_PARAMS:
            typed[pname] = None
        elif pspec.get("required"):
            errors.append(f"line {lineno}: missing required param '{pname}'")
        else:
            default = pspec.get("default")
            if isinstance(default, str) and _base_type(pspec.get("type", "str")) in (
                "float", "int", "bool", "vec3", "vec4",
            ):
                try:
                    typed[pname] = coerce(pspec.get("type", "str"), default, pname)
                except ValueError:
                    typed[pname] = default
            else:
                typed[pname] = copy.deepcopy(default)
    if "name" in raw and "name" in allow_extra:
        typed["name"] = raw["name"]
    _apply_offline_rules(key, typed, warnings, errors, lineno)
    if errors:
        raise ValidationError(errors)
    return ValidatedAction(key=key, params=typed, warnings=warnings)


def help_line(key: str, spec: dict) -> str:
    """One-line signature for the GUI action list."""
    parts = []
    for pname, pspec in effective_params(key, spec).items():
        pspec = pspec if isinstance(pspec, dict) else {}
        default = pspec.get("default")
        if pname in AUTO_PARAMS:
            parts.append(f"[{pname}=auto]")
        elif pspec.get("required"):
            parts.append(f"{pname}=<{pspec.get('type', 'str')}>")
        elif default is None:
            parts.append(f"[{pname}]")
        else:
            parts.append(f"[{pname}={default}]")
    if key.startswith("create.") and "name" not in effective_params(key, spec):
        parts.append("[name]")
    sig = " ".join(parts)
    return f"{key} {sig}".rstrip()
