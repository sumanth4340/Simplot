"""Thin multi-agent supervisor: run validated dispatch blocks.

Stdlib only, import-standalone: all reasoner modules arrive via ``deps``
(a namespace with thinker, protocol, dispatcher, catalog, routing,
signatures), exactly like run_eval wires them. No LangGraph, no langchain.

Semantics (v1, deterministic):
  * The block is validated with dispatcher.validate_block first; a bad
    block fails clean with zero steps run.
  * Each STEP runs thinker.plan for that agent (task text prefixed with
    [agent/do], that agent's routing entries as skill context) and every
    emitted line is protocol-validated. A failed STEP stops the run;
    later STEPs are reported skipped (same stop-short policy as the GUI
    batch runner). A STEP that emits zero lines is ok with a warning.
  * PARALLEL agents=a+b runs the following consecutive member STEPs
    concurrently (threads, isolated snapshots). COWORK runs them in
    plan order with a blackboard: each member's snapshot carries the
    prior members' emitted lines.
  * DEPLOY needs=a+b is enforced: an agent's STEP fails unless every
    needs-agent already has a completed ok STEP. Inside one PARALLEL
    group the check runs against pre-group state, so intra-group deps
    must use COWORK or sequential order instead.
  * DONE ends the plan (later ops ignored). Comments/DONE alone form a
    valid empty plan.
  * When xval is deployed and steps ran, a verdict re-validates every
    emitted line and aggregates the run status. final_text concatenates
    the ok steps' lines in STEP order for the caller to execute.

Run: python -c "from supervisor import run_block; ..." (see tests).
"""
from __future__ import annotations

import concurrent.futures

__all__ = ["run_block", "is_dispatch_text", "task_from_comments",
           "format_log", "format_agent_lines", "step_results",
           "failure_outcome", "combine_outcome"]


def _agent_skills(agent, task, thinker, routing, dispatcher):
    """Routing entries for one agent, else task-selected skills + note."""
    pack = (dispatcher.AGENT_PACKS or {}).get(agent, "")
    hits = [e for e in (routing or [])
            if agent in (str(e.get("skill") or ""), str(e.get("name") or ""))
            or (pack and pack in str(e.get("path") or ""))]
    if hits:
        return hits, []
    return list(thinker.select_skills(task, routing)), [
        f"no routing entry for agent {agent!r}; used task skills"]


def _run_step(op, task, snapshot, deps, config, guided_regex=None):
    """Execute one STEP op -> step result dict (never raises)."""
    thinker, protocol = deps.thinker, deps.protocol
    n = int(op["args"]["n"])
    agent, do = op["args"]["agent"], op["args"]["do"]
    skills, notes = _agent_skills(agent, task, thinker, deps.routing,
                                  deps.dispatcher)
    try:
        plan = thinker.plan(f"[{agent}/{do}] {task}", snapshot,
                            deps.signatures, skills,
                            known_keys=set(deps.catalog), config=config,
                            guided_regex=guided_regex)
        text = plan.actions_text or ""
    except Exception as exc:
        return {"n": n, "agent": agent, "do": do, "lines": "",
                "valid": 0, "total": 0, "ok": False, "backend": "?",
                "notes": notes, "errors": [f"planner failed: {exc}"[:160]]}
    try:
        batch = protocol.parse_batch(text)
    except Exception as exc:
        return {"n": n, "agent": agent, "do": do, "lines": text,
                "valid": 0, "total": 0, "ok": False,
                "backend": getattr(plan, "backend", "?"),
                "notes": notes + list(getattr(plan, "notes", []) or []),
                "errors": [f"unparsable plan: {exc}"[:160]]}
    valid, errors = 0, []
    for key, raw, lineno in batch:
        try:
            protocol.validate(key, raw, deps.catalog, lineno=lineno)
            valid += 1
        except (protocol.ValidationError, protocol.ProtocolError) as exc:
            errors.append(f"line {lineno}: {exc}"[:160])
    step_notes = notes + list(getattr(plan, "notes", []) or [])
    if not batch:
        step_notes = step_notes + ["step emitted no lines"]
    return {"n": n, "agent": agent, "do": do, "lines": text,
            "valid": valid, "total": len(batch),
            "ok": valid == len(batch),
            "backend": getattr(plan, "backend", "?"),
            "notes": step_notes, "errors": errors[:3]}


def _needs_ready(agent, deployed, completed):
    return [b for b in deployed.get(agent, [])
            if completed.get(b, 0) < 1]


def _fail_result(text_err, steps, groups, verdict_notes=None):
    return {"ok": False, "error": text_err, "steps": steps,
            "skipped": [], "groups": groups,
            "verdict": {"ok": False, "checked": 0, "valid": 0,
                        "notes": verdict_notes or [text_err]},
            "final_text": "", "final_lines": [], "backends": []}


def run_block(text, task, snapshot, deps, config=None, max_workers=8,
              guided_regex=None):
    """Validate and run a dispatch block -> result dict (never raises)."""
    try:
        ops = deps.dispatcher.validate_block(text)
    except deps.dispatcher.DispatchError as exc:
        return _fail_result(f"invalid dispatch block: {exc}", [], [])
    except Exception as exc:
        return _fail_result(f"dispatch validation crashed: {exc}", [], [])
    runnable = [op for op in ops if op["verb"] not in ("#", "DONE")]
    if not runnable:
        return {"ok": True, "error": "", "steps": [], "skipped": [],
                "groups": [],
                "verdict": {"ok": True, "checked": 0, "valid": 0,
                            "notes": ["empty plan"]},
                "final_text": "", "final_lines": [], "backends": []}

    deployed, completed = {}, {}
    steps, groups = [], []
    board = []
    i, stop_err = 0, ""
    while i < len(ops):
        op = ops[i]
        verb = op["verb"]
        if verb in ("#",):
            i += 1
            continue
        if verb == "DONE":
            break
        if verb == "DEPLOY":
            agent = op["args"]["agent"]
            needs = op["args"].get("needs", "")
            deployed[agent] = needs.split("+") if needs else []
            i += 1
            continue
        if verb in ("PARALLEL", "COWORK"):
            members = op["args"]["agents"].split("+")
            js = []
            j = i + 1
            while (j < len(ops) and ops[j]["verb"] == "STEP"
                   and ops[j]["args"].get("agent") in members):
                js.append(j)
                j += 1
            groups.append({"verb": verb, "agents": members,
                           "steps": [int(ops[k]["args"]["n"]) for k in js],
                           "mode": "threads" if verb == "PARALLEL"
                           else "blackboard"})
            if not js:
                i = j
                continue
            if verb == "PARALLEL":
                unready = {int(ops[k]["args"]["n"]): _needs_ready(
                    ops[k]["args"]["agent"], deployed, completed) for k in js}
                bad = {n: m for n, m in unready.items() if m}
                if bad:
                    n0 = min(bad)
                    stop_err = (f"step {n0} blocked: needs "
                                f"{bad[n0]} have no completed step yet")
                    i = j
                    break
                with concurrent.futures.ThreadPoolExecutor(
                        max_workers=min(len(js), max(1, max_workers))) as pool:
                    got = list(pool.map(
                        lambda k: _run_step(ops[k], task, snapshot, deps,
                                            config, guided_regex), js))
                for res in sorted(got, key=lambda r: r["n"]):
                    steps.append(res)
                    if res["ok"]:
                        completed[res["agent"]] = completed.get(
                            res["agent"], 0) + 1
                failed = [r for r in got if not r["ok"]]
                if failed:
                    n0 = min(r["n"] for r in failed)
                    stop_err = f"step {n0} failed; run stopped"
                    i = j
                    break
            else:
                for k in js:
                    res = _run_step_cowork(ops[k], task, snapshot, board,
                                           deps, config, deployed,
                                           completed, guided_regex)
                    if res is None:
                        ag = ops[k]["args"]["agent"]
                        missing = _needs_ready(ag, deployed, completed)
                        stop_err = (
                            f"step {ops[k]['args']['n']} blocked: needs "
                            f"{missing} have no completed step yet")
                        break
                    steps.append(res)
                    if res["ok"]:
                        completed[res["agent"]] = completed.get(
                            res["agent"], 0) + 1
                        if res["lines"].strip():
                            board.append(f"# {res['agent']} step {res['n']}:")
                            board.append(res["lines"].rstrip())
                    else:
                        stop_err = (f"step {res['n']} failed; run stopped")
                        break
                else:
                    i = j
                    continue
                break
            i = j
            continue
        # plain STEP
        agent = op["args"]["agent"]
        missing = _needs_ready(agent, deployed, completed)
        if missing:
            stop_err = (f"step {op['args']['n']} blocked: needs "
                        f"{missing} have no completed step yet")
            break
        res = _run_step(op, task, snapshot, deps, config, guided_regex)
        steps.append(res)
        if res["ok"]:
            completed[agent] = completed.get(agent, 0) + 1
        else:
            stop_err = f"step {res['n']} failed; run stopped"
            break
        i += 1

    ran = {s["n"] for s in steps}
    skipped = sorted(int(op["args"]["n"]) for op in ops
                     if op["verb"] == "STEP" and int(op["args"]["n"]) not in ran)
    ok_steps = [s for s in steps if s["ok"]]
    final_lines = []
    for s in sorted(ok_steps, key=lambda r: r["n"]):
        final_lines += [ln for ln in s["lines"].splitlines() if ln.strip()]
    backends = sorted({s["backend"] for s in steps})
    ok = not stop_err
    if "xval" in deployed and steps:
        checked, valid = 0, 0
        for s in ok_steps:
            try:
                batch = deps.protocol.parse_batch(s["lines"])
            except Exception:
                continue
            for key, raw, lineno in batch:
                checked += 1
                try:
                    deps.protocol.validate(key, raw, deps.catalog,
                                           lineno=lineno)
                    valid += 1
                except (deps.protocol.ValidationError,
                        deps.protocol.ProtocolError):
                    pass
        notes = [f"xval re-validated {valid}/{checked} emitted lines"]
        if not ok:
            notes.append(stop_err)
        verdict = {"ok": ok and valid == checked, "checked": checked,
                   "valid": valid, "notes": notes}
        ok = verdict["ok"]
        if not ok and not stop_err:
            stop_err = (f"xval verdict FAIL: {checked - valid} lines "
                        f"failed re-validation")
    elif "xval" in deployed:
        verdict = {"ok": ok, "checked": 0, "valid": 0,
                   "notes": ["xval deployed; no steps ran"]}
    else:
        verdict = {"ok": ok, "checked": 0, "valid": 0,
                   "notes": ["single-agent run, no xval deployed"]
                   if ok else [stop_err]}
    return {"ok": ok, "error": "" if ok else stop_err, "steps": steps,
            "skipped": skipped, "groups": groups, "verdict": verdict,
            "final_text": "\n".join(final_lines) + ("\n" if final_lines else ""),
            "final_lines": final_lines, "backends": backends}


def _run_step_cowork(op, task, snapshot, board, deps, config, deployed,
                     completed, guided_regex=None):
    """One COWORK member step, or None when its needs are unready."""
    if _needs_ready(op["args"]["agent"], deployed, completed):
        return None
    snap = snapshot
    if board:
        snap = (snapshot.rstrip() + "\n\nPRIOR COWORK LINES:\n"
                + "\n".join(board) + "\n")
    return _run_step(op, task, snap, deps, config, guided_regex)


_VERBS = ("DEPLOY", "STEP", "PARALLEL", "COWORK")


def is_dispatch_text(text) -> bool:
    """True when any line opens with a dispatch verb (exact, uppercase).

    Dotted action keys (sim.step), bare DONE, and # comments do not
    count, so pure action batches keep their exact current behavior.
    """
    for line in (text or "").splitlines():
        head = line.strip().split(None, 1)
        if head and head[0] in _VERBS:
            return True
    return False


def task_from_comments(text) -> str:
    """First non-blank # comment -> task fallback (bridge has no task box)."""
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            task = stripped[1:].strip()
            if task:
                return task
    return ""


def format_log(res) -> list:
    """Supervisor result -> human log lines (steps, groups, verdict)."""
    lines = []
    if not res.get("ok") and res.get("error"):
        lines.append("ERROR: " + res["error"])
    for step in res.get("steps", []):
        lines.append(f"step {step['n']} {step['agent']}/{step['do']}: "
                     f"valid {step['valid']}/{step['total']} "
                     f"({step['backend']})")
        for err in step.get("errors", []):
            lines.append("  ERROR: " + err)
    for group in res.get("groups", []):
        lines.append(f"{group['verb']} {'+'.join(group['agents'])}: "
                     f"{len(group['steps'])} step(s) ({group['mode']})")
    verdict = res.get("verdict", {})
    lines.append(f"verdict: {'ok' if verdict.get('ok') else 'FAIL'} "
                 f"({'; '.join(verdict.get('notes', []))})")
    if res.get("skipped"):
        lines.append(f"skipped steps: {res['skipped']}")
    return lines


def format_agent_lines(res, max_per_step: int = 8) -> list:
    """Per-agent emitted action lines for display (GUI/bridge log).

    Read-only view over a run_block result: one header per ran
    step plus its emitted lines verbatim, capped per step so a
    chatty agent cannot flood the log. Empty when no steps ran.
    """
    cap = max(0, int(max_per_step))
    lines = []
    for step in res.get("steps", []):
        emitted = [ln.strip()
                   for ln in (step.get("lines") or "").splitlines()
                   if ln.strip()]
        lines.append(f"agent {step['agent']} step {step['n']} "
                     f"({step['do']}) emitted {len(emitted)} line(s):")
        for ln in emitted[:cap]:
            lines.append("  " + ln)
        if len(emitted) > cap:
            lines.append(f"  ... +{len(emitted) - cap} more")
    return lines


def step_results(res) -> list:
    """Per-step entries in the window/bridge result shape."""
    out = []
    for step in res.get("steps", []):
        msg = f"{step['do']}: valid {step['valid']}/{step['total']}"
        if step.get("errors"):
            msg += "; " + "; ".join(step["errors"])
        out.append({"key": f"step{step['n']}:{step['agent']}", "line": 0,
                    "ok": step["ok"], "msg": msg})
    return out


def failure_outcome(text, res) -> dict:
    """Window/bridge outcome for a failed dispatch run (nothing executed)."""
    return {"ok": False,
            "lines": [ln.strip() for ln in (text or "").splitlines()
                      if ln.strip()],
            "results": step_results(res),
            "log": format_log(res),
            "events": []}


def combine_outcome(res, exec_outcome) -> dict:
    """Merge a supervisor result with its executed-lines outcome.

    Step summaries come first, then the per-line execution results;
    events stay empty here — the caller fills them from its own
    watchdog boundary diff over the whole dispatch run.
    """
    return {"ok": bool(exec_outcome["ok"]),
            "lines": list(exec_outcome["lines"]),
            "results": step_results(res) + list(exec_outcome["results"]),
            "log": format_log(res) + list(exec_outcome["log"]),
            "events": []}
