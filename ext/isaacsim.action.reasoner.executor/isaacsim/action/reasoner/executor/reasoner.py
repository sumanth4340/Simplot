"""In-GUI Reasoner loop policy: task -> observe -> plan -> act -> verify.

Stdlib only on purpose: no omni/isaac imports, so this module can be
unit-tested with a plain python outside Isaac Sim, exactly like
protocol.py, thinker.py, and bridge.py.

The GUI (window.py) drives the loop; this module holds the pure policy:
DONE-verdict parsing, retry-task building, and stop decisions. Every
stage mutation still goes through validated catalog actions via the
executor — the Reasoner never runs code, only action lines.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MAX_STEPS_DEFAULT = 6
VERDICT_DONE = "DONE"


@dataclass
class StepRecord:
    """One executed loop step: the plan plus its per-line results."""
    step: int
    actions_text: str
    backend: str  # "glimmer", "mock", or "reflex"
    results: list  # [{"key", "line", "ok", "msg"}, ...] like the executor
    ok: bool


@dataclass
class ReasonerSession:
    """Loop state for one task. The GUI owns the instance."""
    task: str
    max_steps: int = MAX_STEPS_DEFAULT
    steps: list = field(default_factory=list)
    status: str = "running"  # running | done | failed | stopped
    reason: str = ""

    def record(self, step: StepRecord) -> None:
        self.steps.append(step)

    def last_ok(self):
        """Outcome of the latest executed step, or None when none ran."""
        if not self.steps:
            return None
        return self.steps[-1].ok

    def failures(self) -> list:
        """FAIL lines of the latest step ([] when it was clean)."""
        if not self.steps:
            return []
        return [f"FAIL [{r.get('key')}] {r.get('msg')}"
                for r in self.steps[-1].results if not r.get("ok")]


def split_verdict(actions_text: str) -> tuple:
    """Split a plan into (is_done, runnable_text).

    A line that is exactly DONE (case-insensitive) is the planner's
    completion verdict; it wins over any co-emitted action lines, which
    are kept in runnable_text only so the caller can log what it ignored.
    """
    kept: list = []
    done = False
    for line in (actions_text or "").splitlines():
        if line.strip().upper() == VERDICT_DONE:
            done = True
            continue
        kept.append(line)
    runnable = "\n".join(kept)
    if runnable and not runnable.endswith("\n"):
        runnable += "\n"
    return done, runnable


def _format_step(step: StepRecord) -> list:
    header = (f"Step {step.step} ({step.backend}): "
              f"{len(step.results)} action(s), "
              f"{'all ok' if step.ok else 'FAILED'}")
    lines = [header]
    for raw in (step.actions_text or "").splitlines():
        if raw.strip():
            lines.append(f"  ran: {raw.strip()}")
    for fail in [f"  {r}" for r in
                 (f"FAIL [{x.get('key')}] {x.get('msg')}"
                  for x in step.results if not x.get("ok"))]:
        lines.append(fail)
    return lines


def build_step_task(session: ReasonerSession) -> str:
    """Task string for the next plan call: plain on step 1, history after."""
    if not session.steps:
        return session.task
    step_no = len(session.steps) + 1
    lines = [session.task,
             f"",
             f"LOOP STATE — you are on step {step_no} of at most "
             f"{session.max_steps}. Previous steps this run:"]
    for step in session.steps:
        lines.extend(_format_step(step))
    lines += [
        "",
        "Fresh snapshot/screenshot attached separately. Reply with ONLY the",
        "next action lines (repairs or follow-ups; never repeat actions",
        "that already succeeded), or ONLY the single line DONE if the",
        "task is fully complete.",
    ]
    return "\n".join(lines)


def check_backend(step_no: int, backend: str):
    """None when the backend may plan this step, else a failure reason.

    The mock planner is deterministic and text-only: fine for a single
    pass, but it cannot observe or repair, so it must not continue a
    loop (re-running its fixed plan would duplicate prims). The reflex
    dispatcher is single-pass for the same reason.
    """
    if step_no > 1 and backend == "mock":
        return ("endpoint unreachable mid-run and the mock planner cannot "
                "continue a loop; fix the endpoint and press Reason again")
    if step_no > 1 and backend == "reflex":
        return ("the reflex dispatcher already ran its single pass; "
                "press Reason again for a fresh run")
    return None


def decide_empty_plan(session: ReasonerSession) -> tuple:
    """Stop decision when the planner emits no runnable lines."""
    if not session.steps:
        return "failed", "planner returned no actions"
    if session.last_ok():
        return "done", "planner returned no further actions; last run clean"
    return "failed", "planner returned no actions after a failed run"


def decide_after_run(session: ReasonerSession, backend: str) -> tuple:
    """Stop decision after recording a step: continue | done | failed."""
    last_ok = session.last_ok()
    if backend == "mock":
        # Single pass: the mock plan is fixed, re-running it would only
        # duplicate what it just built.
        if last_ok:
            return "done", "mock single pass complete, all lines ok"
        return "failed", "mock single pass failed; configure the Glimmer endpoint for repairs"
    if backend == "reflex":
        # Single pass: a reflex hit means the whole task was primitive,
        # so there is nothing further to verify or repair.
        if last_ok:
            return "done", "reflex single pass complete, all lines ok"
        return "failed", "reflex single pass failed; rephrase or press Think"
    ran = len(session.steps)
    if ran >= session.max_steps:
        if last_ok:
            return "done", f"step budget reached ({ran}/{session.max_steps}); last run clean"
        return "failed", f"step budget exhausted ({ran}/{session.max_steps})"
    if last_ok:
        return "continue", "verifying with a fresh observation"
    return "continue", "repairing after failure"
