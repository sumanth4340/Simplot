"""Dispatcher grammar: thinker -> skill-agent deploy plans as logic lines.

Stdlib only on purpose: no omni/isaac imports, so this module can be
unit-tested with a plain python outside Isaac Sim, exactly like
protocol.py, thinker.py, and reasoner.py.

A dispatch block assigns a composite task to the 18 appointed agents
(see action-reasoner/AGENTS.md). Every line is machine-checkable; no
prose is ever valid here. Agents reply with catalog action lines; the
thinker plans with these verbs:

    DEPLOY agent=<name> [needs=<a+b+...>]
    STEP n=<int> agent=<name> do=<slug>
    PARALLEL agents=<a+b+...>
    COWORK agents=<a+b+...>
    DONE                                    (plan complete, no deploy)
    # comment                               (transcript only)

Rules:
  * agent names must be in ROSTER; sets use + with no spaces, no dupes.
  * every agent used in STEP/PARALLEL/COWORK needs exactly one DEPLOY,
    and the DEPLOY must come before its first use.
  * STEP n starts at 1 and increases by 1 in block order.
  * more than one non-xval agent deployed requires xval (the gauntlet).
  * values carry no spaces; `do` is a slug, not a sentence.
  * comments/DONE alone validate as an empty plan (no deploy).
"""
from __future__ import annotations

import re

ROSTER = (
    "sense", "stage", "modeling", "articulation", "manipulation",
    "rendering", "viewport", "omnigraph", "behavior", "appsession",
    "physics", "pyapi", "deform", "gpunuc", "rosnav", "sensors",
    "sdg", "xval",
)

AGENT_PACKS = {
    "sense": "workspace-sense",
    "stage": "stage-core",
    "modeling": "modeling-assets",
    "articulation": "articulation-robots",
    "manipulation": "manipulation-motion",
    "rendering": "rendering-lighting",
    "viewport": "viewport-ui",
    "omnigraph": "omnigraph",
    "behavior": "behavior-anim",
    "appsession": "app-session",
    "physics": "physics",
    "pyapi": "pyapi",
    "deform": "deform",
    "gpunuc": "gpunuc",
    "rosnav": "ros-navigation",
    "sensors": "sensors",
    "sdg": "sdg",
    "xval": "cross-val",
}

_VERBS = ("DEPLOY", "STEP", "PARALLEL", "COWORK")
_VERB_KEYS = {
    "DEPLOY": ("agent", "needs"),
    "STEP": ("n", "agent", "do"),
    "PARALLEL": ("agents",),
    "COWORK": ("agents",),
}
_SLUG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+/-]*$")
_KV_RE = re.compile(r"^([A-Za-z_]+)=(\S+)$")


class DispatchError(Exception):
    """Raised when a dispatch block breaks the grammar or roster rules."""


def _parse_set(raw: str, what: str, lineno: int) -> list:
    if not raw or "+" in raw and "" in raw.split("+"):
        raise DispatchError(f"line {lineno}: bad {what} set {raw!r}")
    names = raw.split("+")
    if len(set(names)) != len(names):
        raise DispatchError(f"line {lineno}: duplicate in {what} {raw!r}")
    for name in names:
        if name not in ROSTER:
            raise DispatchError(
                f"line {lineno}: unknown agent {name!r} (not in roster)")
    return names


def parse_block(text: str) -> list:
    """Parse a dispatch block into ops; comments/DONE kept as markers.

    Returns a list of {"verb", "args", "lineno"} dicts. Raises
    DispatchError on the first malformed line.
    """
    ops = []
    for lineno, raw_line in enumerate((text or "").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            ops.append({"verb": "#", "args": {}, "lineno": lineno})
            continue
        if line.upper() == "DONE":
            ops.append({"verb": "DONE", "args": {}, "lineno": lineno})
            continue
        parts = line.split()
        verb = parts[0]
        if verb not in _VERBS:
            raise DispatchError(
                f"line {lineno}: bad verb {verb!r} (want {', '.join(_VERBS)})")
        args = {}
        for tok in parts[1:]:
            m = _KV_RE.match(tok)
            if not m:
                raise DispatchError(
                    f"line {lineno}: bad token {tok!r} (want k=v, no spaces)")
            key, val = m.group(1), m.group(2)
            if key not in _VERB_KEYS[verb]:
                raise DispatchError(
                    f"line {lineno}: bad key {key!r} for {verb}")
            if key in args:
                raise DispatchError(
                    f"line {lineno}: duplicate key {key!r}")
            args[key] = val
        ops.append({"verb": verb, "args": args, "lineno": lineno})
    return ops


def validate_block(text: str) -> list:
    """Validate a dispatch block; return ops or raise DispatchError."""
    ops = parse_block(text)
    deployed: dict = {}
    step_want = 1
    runnable = [op for op in ops if op["verb"] not in ("#", "DONE")]
    if not runnable:
        return ops  # comments/DONE only: valid empty plan (no deploy)
    for op in runnable:
        verb, args, lineno = op["verb"], op["args"], op["lineno"]
        if verb == "DEPLOY":
            agent = args.get("agent", "")
            if agent not in ROSTER:
                raise DispatchError(
                    f"line {lineno}: unknown agent {agent!r}")
            if agent in deployed:
                raise DispatchError(
                    f"line {lineno}: duplicate DEPLOY {agent!r}")
            needs = []
            if "needs" in args:
                needs = _parse_set(args["needs"], "needs", lineno)
                if agent in needs:
                    raise DispatchError(
                        f"line {lineno}: agent cannot need itself")
            deployed[agent] = needs
        elif verb == "STEP":
            try:
                n = int(args.get("n", ""))
            except ValueError:
                raise DispatchError(
                    f"line {lineno}: bad STEP n={args.get('n', '')!r}")
            if n != step_want:
                raise DispatchError(
                    f"line {lineno}: STEP n={n} breaks order (want {step_want})")
            step_want += 1
            agent = args.get("agent", "")
            if agent not in ROSTER:
                raise DispatchError(
                    f"line {lineno}: unknown agent {agent!r}")
            if agent not in deployed:
                raise DispatchError(
                    f"line {lineno}: STEP uses undeployed agent {agent!r}")
            do = args.get("do", "")
            if not _SLUG_RE.match(do):
                raise DispatchError(
                    f"line {lineno}: bad STEP do={do!r} (want slug, no spaces)")
        else:  # PARALLEL / COWORK
            agents = _parse_set(args.get("agents", ""), "agents", lineno)
            for agent in agents:
                if agent not in deployed:
                    raise DispatchError(
                        f"line {lineno}: {verb} uses undeployed {agent!r}")
    workers = [a for a in deployed if a != "xval"]
    if len(workers) > 1 and "xval" not in deployed:
        raise DispatchError(
            f"multi-agent plan ({', '.join(workers)}) needs xval deployed")
    return ops


def is_dispatch_line(line: str) -> bool:
    """True when the line opens with a dispatch verb, DONE, or #."""
    head = (line or "").strip().split(None, 1)
    if not head:
        return False
    return head[0] in _VERBS or head[0].upper() == "DONE" or line.strip().startswith("#")


def describe_roster() -> list:
    """One 'agent -> pack' line per agent, for prompt building."""
    return [f"- {agent}: skills/{AGENT_PACKS[agent]}/" for agent in ROSTER]
