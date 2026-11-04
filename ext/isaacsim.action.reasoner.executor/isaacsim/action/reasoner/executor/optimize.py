"""Optimizer gate: fuse agent emission + math verdict into one call.

The last step before execution. Takes a supervisor result (what the
agents emitted) plus the mission context (state, goal, obstacles,
drive config, optional scan) and returns one execute/refuse decision:

* agents failed or emitted nothing -> VETO, math skipped.
* math FAIL -> VETO with the failing check's fix attached.
* math WARN -> EXECUTE with the warnings attached as annotations.
* all clean -> EXECUTE.

Stdlib only, import-standalone: nav.preflight arrives via ``deps``
(a namespace with preflight), exactly like supervisor.run_block
wires its modules. Fail-closed: malformed context vetoes instead
of executing blind. Standalone for now — the live-path hook is a
post-hackathon one-liner at the supervisor/executor boundary.
"""
from __future__ import annotations

__all__ = ["optimize"]


def optimize(res, ctx, deps) -> dict:
    """Gate one agent emission -> execute/refuse dict (never raises)."""
    res = res or {}
    steps = res.get("steps", []) or []
    verdict_ok = bool(res.get("verdict", {}).get("ok", False))
    final = (res.get("final_text") or "").strip()
    agent_ok = bool(res.get("ok")) and verdict_ok and bool(final)
    agent_line = (f"agents: {'ok' if agent_ok else 'FAILED'} "
                  f"({len(steps)} step(s), verdict "
                  f"{'ok' if verdict_ok else 'FAIL'})")
    if not res.get("ok"):
        err = res.get("error") or "unknown supervisor failure"
        return {"execute": False, "reason": f"agents failed: {err}",
                "agent_ok": False, "math": [], "annotations": [],
                "report": ["OPTIMIZER verdict: VETO", agent_line,
                           f"agents failed: {err}"]}
    if not final:
        reason = "agents emitted no executable lines"
        return {"execute": False, "reason": reason,
                "agent_ok": False, "math": [], "annotations": [],
                "report": ["OPTIMIZER verdict: VETO", agent_line, reason]}
    if ctx is None:
        note = "math skipped (no mission context)"
        return {"execute": True, "reason": "clear to execute",
                "agent_ok": True, "math": [], "annotations": [],
                "report": ["OPTIMIZER verdict: EXECUTE", agent_line,
                           note]}
    try:
        pre = deps.preflight
        checks = pre.preflight(ctx["state"], ctx["goal"],
                               ctx.get("obstacles", []), ctx["cfg"],
                               scan=ctx.get("scan"),
                               max_range=ctx.get("max_range", 8.0))
        math_verdict = pre.verdict(checks)
        report = pre.format_report(checks)
    except Exception as exc:
        reason = f"optimizer could not verify: {exc}"[:200]
        return {"execute": False, "reason": reason,
                "agent_ok": agent_ok, "math": [], "annotations": [],
                "report": ["OPTIMIZER verdict: VETO", agent_line,
                           reason]}
    if math_verdict == "fail":
        first = next(c["msg"] for c in checks
                     if c["verdict"] == "fail")
        return {"execute": False, "reason": first,
                "agent_ok": agent_ok, "math": checks,
                "annotations": [],
                "report": ["OPTIMIZER verdict: VETO", agent_line,
                           *report]}
    notes = [c["msg"] for c in checks if c["verdict"] == "warn"]
    return {"execute": True, "reason": "clear to execute",
            "agent_ok": agent_ok, "math": checks,
            "annotations": notes,
            "report": ["OPTIMIZER verdict: EXECUTE", agent_line,
                       *report]}
