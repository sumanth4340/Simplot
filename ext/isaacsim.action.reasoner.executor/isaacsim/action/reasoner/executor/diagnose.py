"""Failure black box: one-shot diagnosis for NOVEL failures.

Preflight kills known errors in milliseconds. This module handles the
rest: it packs a failure — the failed line, the error, before/after
snapshots, recent trace — into one evidence bundle plus one LLM task
string, so a novel failure gets diagnosed in a single model call
instead of a multi-leg flail.

Stdlib only, import-standalone: the thinker arrives via ``deps`` (a
namespace with thinker, catalog, signatures), exactly like
supervisor.run_block wires it. The model replies in action lines
only: a 1-3 line fix, or NO-FIX plus the single most informative
next probe line.
"""
from __future__ import annotations

import difflib

__all__ = ["snapshot_delta", "capture_failure", "build_diagnosis_task",
           "split_no_fix", "summarize_failure", "diagnose"]

NO_FIX = "NO-FIX"


def snapshot_delta(before: str, after: str, cap: int = 12) -> dict:
    """Line diff of two snapshots -> added/removed/changed, capped.

    ``changed`` holds (before, after) line pairs. Each list keeps at
    most ``cap`` entries; overflow lands in ``<name>_truncated``
    counts (present only when nonzero) so prompts stay small.
    """
    old = (before or "").splitlines()
    new = (after or "").splitlines()
    added, removed, changed = [], [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            a=old, b=new, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            for a, b in zip(old[i1:i2], new[j1:j2]):
                changed.append((a, b))
            # uneven replaces spill the leftovers to added/removed
            removed.extend(old[i1:i2][len(new[j1:j2]):])
            added.extend(new[j1:j2][len(old[i1:i2]):])
        elif tag == "delete":
            removed.extend(old[i1:i2])
        elif tag == "insert":
            added.extend(new[j1:j2])
    out = {"added": added[:cap], "removed": removed[:cap],
           "changed": changed[:cap]}
    if len(added) > cap:
        out["added_truncated"] = len(added) - cap
    if len(removed) > cap:
        out["removed_truncated"] = len(removed) - cap
    if len(changed) > cap:
        out["changed_truncated"] = len(changed) - cap
    return out


def capture_failure(task: str, line: str, lineno: int, key: str,
                    msg: str, stage: str, shot_before: str,
                    shot_after: str, trace_tail=()) -> dict:
    """Pack one failure into a black-box evidence bundle (never raises).

    ``stage`` is where the line died: "parse", "validate", or "exec"
    (the caller knows; nothing here guesses from message text).
    """
    delta = snapshot_delta(shot_before or "", shot_after or "")
    changed = bool(delta["added"] or delta["removed"] or delta["changed"])
    return {"task": task or "", "line": line or "", "lineno": lineno,
            "key": key or "", "msg": msg or "", "stage": stage or "",
            "shot_before": shot_before or "",
            "shot_after": shot_after or "",
            "trace_tail": list(trace_tail or []),
            "stage_changed": changed, "delta": delta}


def _delta_lines(delta: dict, cap: int = 12) -> list:
    lines = []
    for old, new in delta.get("changed", [])[:cap]:
        lines.append(f"  ~ {old}  ->  {new}")
    for ln in delta.get("added", [])[:cap]:
        lines.append(f"  + {ln}")
    for ln in delta.get("removed", [])[:cap]:
        lines.append(f"  - {ln}")
    left = (delta.get("added_truncated", 0)
            + delta.get("removed_truncated", 0)
            + delta.get("changed_truncated", 0))
    if left:
        lines.append(f"  ... +{left} more delta line(s)")
    return lines or ["  (stage unchanged)"]


def build_diagnosis_task(failure: dict, signatures=()) -> str:
    """Black box -> one LLM task string; fix comes back action-only."""
    changed = "yes" if failure.get("stage_changed") else "no"
    lines = [
        f"TASK: {failure.get('task', '')}",
        "",
        "SYMPTOM — this action line just failed:",
        f"  line {failure.get('lineno')}: {failure.get('line', '')}",
        f"  key: {failure.get('key', '') or '(unparsed)'}",
        f"  failed at stage: {failure.get('stage', '')}",
        f"  error: {failure.get('msg', '')}",
        "",
        f"EVIDENCE — stage_changed={changed}. Snapshot delta:",
    ]
    lines.extend(_delta_lines(failure.get("delta", {})))
    tail = failure.get("trace_tail") or []
    lines.append("Recent trace (newest last):")
    lines.extend(f"  {ln}" for ln in tail[-6:])
    if signatures:
        lines.append("")
        lines.append("Valid action signatures for the fix:")
        lines.extend(f"  {sig}" for sig in signatures)
    lines += [
        "",
        "Reply with ONLY action lines: a 1-3 line fix for the failed",
        "step (corrected args, a missing setup line first, or a safe",
        "alternative) — or the single line NO-FIX followed by the one",
        "most informative next probe line. Never prose, never fences,",
        "never repeat the failed line unchanged.",
    ]
    return "\n".join(lines)


def split_no_fix(actions_text: str) -> tuple:
    """Split a diagnosis reply into (is_no_fix, probe_text)."""
    kept: list = []
    no_fix = False
    for line in (actions_text or "").splitlines():
        if line.strip().upper() == NO_FIX:
            no_fix = True
            continue
        kept.append(line)
    probe = "\n".join(kept)
    if probe and not probe.endswith("\n"):
        probe += "\n"
    return no_fix, probe


def summarize_failure(failure: dict) -> str:
    """One-line black-box record for the GUI/bridge log."""
    changed = "yes" if failure.get("stage_changed") else "no"
    return (f"blackbox [{failure.get('stage', '')}] "
            f"line {failure.get('lineno')}: "
            f"{failure.get('key', '') or '(unparsed)'} "
            f"'{(failure.get('msg', '') or '')[:100]}' "
            f"stage_changed={changed}")


def diagnose(failure: dict, deps, skills=(), config=None,
             guided_regex=None) -> dict:
    """One model call -> fix lines or a NO-FIX probe (never raises)."""
    task = build_diagnosis_task(failure, getattr(deps, "signatures", ()))
    try:
        plan = deps.thinker.plan(
            task, failure.get("shot_after", ""),
            getattr(deps, "signatures", ()), list(skills or ()),
            known_keys=set(getattr(deps, "catalog", {}) or {}),
            config=config, guided_regex=guided_regex)
        text = plan.actions_text or ""
        backend = getattr(plan, "backend", "?")
        notes = list(getattr(plan, "notes", []) or [])
    except Exception as exc:
        return {"fix_text": "", "no_fix": True, "probe_text": "",
                "backend": "?", "notes": [f"diagnoser failed: {exc}"[:160]]}
    no_fix, probe = split_no_fix(text)
    if no_fix:
        return {"fix_text": "", "no_fix": True, "probe_text": probe,
                "backend": backend, "notes": notes}
    return {"fix_text": text, "no_fix": False, "probe_text": "",
            "backend": backend, "notes": notes}
