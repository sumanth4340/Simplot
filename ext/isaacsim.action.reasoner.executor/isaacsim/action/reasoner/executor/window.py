"""Prompt GUI: the live window where you type actions."""
from __future__ import annotations

import asyncio
import datetime
import json
import queue
import threading
import types
from pathlib import Path

from omni import ui

import omni.timeline

from . import dispatcher as dispatcher_mod
from . import protocol as protocol_mod
from . import supervisor as supervisor_mod
from . import thinker as thinker_mod
from .bridge import (
    default_bridge_dir,
    ensure_layout,
    process_inbox,
    read_status,
    update_result_shot,
    write_status,
)
from .dispatcher import describe_roster, validate_block as dispatcher_validate
from .handlers import HANDLED_ACTIONS, Executor
from .observer import (
    capture_viewport,
    default_capture_dir,
    describe as observer_describe,
    next_capture_path,
)
from .protocol import (
    ProtocolError,
    ValidationError,
    help_line,
    load_catalog,
    parse_batch,
    parse_line,
    validate,
)
from .reasoner import (
    MAX_STEPS_DEFAULT,
    ReasonerSession,
    StepRecord,
    build_step_task,
    check_backend,
    decide_after_run,
    decide_empty_plan,
    split_verdict,
)
from .reflex import try_reflex
from .thinker import (
    ThinkerPlan,
    load_config,
    load_guided_regex,
    plan as thinker_plan,
    plan_dispatch as thinker_plan_dispatch,
    plan_stream as thinker_plan_stream,
    select_skills,
)
from .watcher import Watcher, capture_compact

DEFAULT_PROMPT = """# one action per line, # starts a comment
create.objects.plane size=20
create.objects.cuboid size=1 pos=0,0,2 color=0.2,0.4,0.9
create.objects.sphere radius=0.4 pos=1.5,0,2
sim.play"""

_LOG_CAP = 500


def _data_path(name: str) -> Path:
    # .../isaacsim/action/reasoner/executor/window.py -> ext root/data/...
    return Path(__file__).resolve().parents[4] / "data" / name


def _catalog_path() -> Path:
    return _data_path("actions_compact.json")


def _routing_path() -> Path:
    return _data_path("skills_routing.json")


TRACE_SUBDIR = "action-reasoner-traces"

BRIDGE_POLL_SECONDS = 1.5

STREAM_DRAIN_SECONDS = 0.05


def _trace_path() -> Path:
    folder = Path.home() / TRACE_SUBDIR
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "traces.jsonl"


def _log_trace(event: dict) -> None:
    """Append one live trace event. Never breaks the GUI on failure."""
    try:
        record = {"ts": datetime.datetime.now().isoformat(), **event}
        with open(_trace_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


class ReasonerWindow:
    def __init__(self):
        self._executor = Executor()
        self._watcher = Watcher()
        try:
            self._catalog = load_catalog(_catalog_path())
        except Exception as exc:
            self._catalog = {}
            boot_error = f"catalog failed to load: {exc}"
        else:
            boot_error = ""
        try:
            self._routing = json.loads(_routing_path().read_text(encoding="utf-8"))
            if not isinstance(self._routing, list):
                self._routing = []
        except Exception as exc:
            self._routing = []
            boot_error += f"; routing failed to load: {exc}" if boot_error else f"routing failed to load: {exc}"
        self._thinker_config = load_config()
        self._last_shot = None
        self._pending_shot = None
        self._think_task = ""
        self._think_run_after = False
        self._think_pending_shot = None
        self._reason_session = None
        self._reason_stop = False
        self._reason_pending_shot = None
        self._stream_queue = queue.Queue()
        self._stream_stop = threading.Event()
        self._stream_busy = False
        self._bridge_on = False
        self._bridge_dirs = None
        self._timeline_subs: list = []
        self._log_lines: list = []
        self._window = ui.Window("Action Reasoner", width=560, height=720)
        with self._window.frame:
            with ui.VStack(spacing=6):
                ui.Label("Thinker task (plain English):")
                self._task = ui.StringField(height=40)
                self._task.model.set_value("make a moon rover with two wheels")
                with ui.HStack(spacing=6, height=0):
                    ui.Button("Think", width=80, clicked_fn=self._on_think)
                    ui.Button("Think & Run", width=110, clicked_fn=self._on_think_run)
                    ui.Button("Reason", width=80, clicked_fn=self._on_reason)
                    ui.Button("Dispatch", width=80, clicked_fn=self._on_dispatch)
                    ui.Button("Stop", width=70, clicked_fn=self._on_reason_stop)
                self._thinker_status = ui.Label("Thinker: " + self._thinker_config.describe())
                ui.Label("Action prompt (one action per line):")
                self._prompt = ui.StringField(multiline=True, height=150)
                self._prompt.model.set_value(DEFAULT_PROMPT)
                with ui.HStack(spacing=6, height=0):
                    ui.Button("Run", width=80, clicked_fn=self._on_run)
                    ui.Button("Snapshot", width=90, clicked_fn=self._on_snapshot)
                    ui.Button("Shots", width=70, clicked_fn=self._on_open_shots)
                    ui.Button("Actions", width=80, clicked_fn=self._on_list_actions)
                    ui.Button("Clear", width=70, clicked_fn=self._on_clear)
                with ui.HStack(spacing=6, height=0):
                    self._bridge_btn = ui.Button(
                        "Bridge: Start", width=110,
                        clicked_fn=self._on_bridge_toggle)
                    self._bridge_status = ui.Label("Bridge: off")
                ui.Label("Log:")
                with ui.ScrollingFrame(
                    height=ui.Fraction(1),
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                ):
                    self._log_label = ui.Label(
                        "", word_wrap=True, alignment=ui.Alignment.LEFT_TOP
                    )
        self._log(f"ready: {len(self._catalog)} catalog actions, "
                  f"{len(HANDLED_ACTIONS)} runnable in v0; {observer_describe()}")
        if boot_error:
            self._log("ERROR: " + boot_error)
        self._watch_timeline()

    def show(self):
        self._window.visible = True

    # -- ui helpers ------------------------------------------------------
    def _log(self, msg: str):
        self._log_lines.extend(msg.splitlines() or [""])
        del self._log_lines[:-_LOG_CAP]
        self._log_label.text = "\n".join(self._log_lines)

    def _on_clear(self):
        self._log_lines = []
        self._log_label.text = ""

    def _on_snapshot(self):
        self._log("--- snapshot ---")
        self._log(self._executor.snapshot())
        target = next_capture_path()
        started, msg = capture_viewport(target, on_done=self._on_capture_done)
        self._log(("shot: " if started else "shot ERROR: ") + msg)
        if started:
            self._pending_shot = str(target)
        else:
            self._pending_shot = None

    def _on_capture_done(self, ok: bool, msg: str):
        self._log(("shot: " if ok else "shot ERROR: ") + msg)
        if ok and getattr(self, "_pending_shot", None):
            self._last_shot = self._pending_shot
        self._pending_shot = None

    def _on_open_shots(self):
        folder = default_capture_dir()
        if not folder.is_dir():
            self._log("shots: no captures yet (press Snapshot first)")
            return
        try:
            import os

            os.startfile(str(folder))  # noqa: S606 - Windows-only GUI helper
        except Exception as exc:
            self._log(f"shots: cannot open {folder}: {exc}")
        else:
            self._log(f"shots: opened {folder}")

    def _on_list_actions(self):
        self._log("--- runnable actions (v0) ---")
        for key in HANDLED_ACTIONS:
            spec = self._catalog.get(key)
            self._log(help_line(key, spec) if spec else key)
        self._log(f"--- +{len(self._catalog) - len(HANDLED_ACTIONS)} catalogued, "
                  "handlers coming ---")

    # -- thinker ---------------------------------------------------------
    def _on_think(self):
        self._think(run_after=False)

    def _on_think_run(self):
        self._think(run_after=True)

    def _think(self, run_after: bool):
        task = self._task.model.get_value_as_string().strip()
        if not task:
            self._log("ERROR: type a Thinker task first")
            return
        if not self._catalog:
            self._log("ERROR: no catalog loaded, cannot plan")
            return
        # Fresh viewport shot first so Glimmer plans from what it can see;
        # planning runs when the capture completes (or at once if capture
        # is unavailable, falling back to the last screenshot).
        self._think_task = task
        self._think_run_after = run_after
        target = next_capture_path(prefix="think")
        started, msg = capture_viewport(target, on_done=self._on_think_shot_done)
        self._log(("shot: " if started else "shot ERROR: ") + msg)
        if started:
            self._think_pending_shot = str(target)
        else:
            self._think_pending_shot = None
            self._run_think(task, run_after)

    def _on_dispatch(self):
        task = self._task.model.get_value_as_string().strip()
        if not task:
            self._log("ERROR: type a task first")
            return
        self._thinker_config = load_config()  # re-read: no restart needed
        skills = select_skills(task, self._routing)
        snapshot = self._executor.snapshot()
        images = [self._last_shot] if self._last_shot else []
        result = thinker_plan_dispatch(
            task,
            snapshot,
            describe_roster(),
            skills,
            config=self._thinker_config,
            images=images,
            guided_regex=load_guided_regex(),
            validate=dispatcher_validate,
        )
        self._thinker_status.text = (
            f"Dispatcher: {self._thinker_config.describe()} -> {result.backend}"
        )
        self._log(f"--- dispatch ({result.backend}) ---")
        for note in result.notes:
            self._log("dispatcher: " + note)
        if result.actions_text.strip():
            self._prompt.model.set_value(result.actions_text)
        else:
            self._log("ERROR: no deploy plan (see notes above)")
        _log_trace({
            "event": "dispatch",
            "task": task,
            "backend": result.backend,
            "skills": result.skills,
            "images": images,
            "snapshot": snapshot,
            "actions": result.actions_text,
            "notes": result.notes,
        })

    def _on_think_shot_done(self, ok: bool, msg: str):
        self._log(("shot: " if ok else "shot ERROR: ") + msg)
        if ok and self._think_pending_shot:
            self._last_shot = self._think_pending_shot
        self._think_pending_shot = None
        self._run_think(self._think_task, self._think_run_after)

    def _run_think(self, task: str, run_after: bool):
        self._thinker_config = load_config()  # re-read: no restart needed
        signatures = [
            help_line(key, self._catalog[key])
            for key in HANDLED_ACTIONS
            if key in self._catalog
        ]
        skills = select_skills(task, self._routing)
        snapshot = self._executor.snapshot()
        images = [self._last_shot] if self._last_shot else []
        if self._last_shot:
            snapshot += f"\nscreenshot: {self._last_shot}"
        reflex_hit = try_reflex(task, snapshot)
        if reflex_hit is not None:
            # Millisecond path: primitive command, no LLM call. The lines
            # still flow through the same validate-then-run path as a plan.
            actions_text, reflex_notes = reflex_hit
            result = ThinkerPlan(actions_text=actions_text,
                                 notes=reflex_notes, skills=[],
                                 backend="reflex")
            self._prompt.model.set_value(result.actions_text)
            self._thinker_status.text = (
                f"Thinker: {self._thinker_config.describe()} -> {result.backend}"
            )
            self._log(f"--- think ({result.backend}) ---")
            for note in result.notes:
                self._log("thinker: " + note)
            _log_trace({
                "event": "think",
                "task": task,
                "backend": result.backend,
                "skills": result.skills,
                "images": images,
                "snapshot": snapshot,
                "actions": result.actions_text,
                "notes": result.notes,
            })
            if run_after:
                self._on_run()
            return
        if self._stream_busy:
            self._log("ERROR: a think stream is already running")
            return
        # Live path: a worker thread reads the SSE stream while the async
        # drain below triggers each line on the main thread as it lands,
        # so Think & Run fires actions mid-reply instead of after it.
        self._stream_busy = True
        self._stream_stop.clear()
        while True:
            try:
                self._stream_queue.get_nowait()
            except queue.Empty:
                break
        self._prompt.model.set_value("")
        self._thinker_status.text = (
            f"Thinker: {self._thinker_config.describe()} -> streaming..."
        )
        skill_names = [str(s.get("skill") or s.get("name")) for s in skills]
        self._log(f"--- think (streaming, "
                  f"{'run' if run_after else 'plan only'}) ---")
        if skill_names:
            self._log("skills: " + ", ".join(skill_names))
        if images:
            self._log(f"vision: sending {len(images)} screenshot(s) to Glimmer")
        worker = threading.Thread(
            target=self._stream_worker,
            args=(task, snapshot, signatures, skills, images),
            daemon=True,
        )
        worker.start()
        try:
            asyncio.ensure_future(
                self._drain_stream(task, snapshot, images, run_after))
        except RuntimeError as exc:
            self._stream_stop.set()
            self._stream_busy = False
            self._log(f"think ERROR: no event loop to stream on: {exc}")

    def _stream_worker(self, task, snapshot, signatures, skills, images):
        """Background SSE read: queue each line; the drain triggers them.

        Runs off the main thread and touches only the thinker + queue —
        never the stage or the UI — so Kit keeps pumping frames live.
        """
        def _sink(line, is_comment):
            self._stream_queue.put(("line", is_comment, line))
            return not self._stream_stop.is_set()

        try:
            result = thinker_plan_stream(
                task,
                snapshot,
                signatures,
                skills,
                known_keys=set(self._catalog),
                config=self._thinker_config,
                images=images,
                guided_regex=load_guided_regex(),
                on_line=_sink,
            )
        except Exception as exc:  # never die silently; the drain reports it
            self._stream_queue.put(("error", str(exc)))
        else:
            self._stream_queue.put(("done", result.backend,
                                    result.notes, result.skills,
                                    result.images))

    async def _drain_stream(self, task, snapshot, images, run_after):
        """Main-thread drain: transcript each line, trigger when running."""
        transcript: list = []
        run_lines: list = []
        results: list = []
        ok_all = True
        try:
            while True:
                try:
                    item = self._stream_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(STREAM_DRAIN_SECONDS)
                    continue
                kind = item[0]
                if kind == "line":
                    _, is_comment, line = item
                    transcript.append(line)
                    self._prompt.model.set_value("\n".join(transcript))
                    if run_after and not is_comment and ok_all:
                        outcome = self._run_single_line(line, len(transcript))
                        for log_line in outcome["log"]:
                            self._log(log_line)
                        run_lines.append(outcome["line"])
                        results.extend(outcome["results"])
                        if not outcome["ok"]:
                            ok_all = False
                            self._stream_stop.set()
                elif kind == "done":
                    _, backend, notes, skill_names, images_used = item
                    self._thinker_status.text = (
                        f"Thinker: {self._thinker_config.describe()} "
                        f"-> {backend}")
                    self._log(f"--- think ({backend}) streamed "
                              f"{len(transcript)} line(s) ---")
                    if images_used:
                        self._log(f"vision: sent {images_used} "
                                  "screenshot(s) to Glimmer")
                    for note in notes:
                        self._log("thinker: " + note)
                    _log_trace({
                        "event": "think",
                        "task": task,
                        "backend": backend,
                        "skills": skill_names,
                        "images": images,
                        "snapshot": snapshot,
                        "actions": "\n".join(transcript),
                        "notes": notes,
                    })
                    if run_after:
                        _log_trace({
                            "event": "run",
                            "streamed": True,
                            "lines": run_lines,
                            "results": results,
                        })
                    break
                else:  # ("error", msg)
                    self._log("think ERROR: " + item[1])
                    break
        finally:
            self._stream_busy = False

    def _run_single_line(self, line: str, lineno: int) -> dict:
        """Validate + run one streamed line -> {"ok", "line", "results", "log"}.

        Same stop-at-first-failure contract as _run_batch_text, which keeps
        serving the Run button and the file bridge for whole batches.
        """
        try:
            parsed = parse_line(line, lineno=lineno)
        except ProtocolError as exc:
            return {"ok": False, "line": line,
                    "results": [{"key": "", "line": lineno, "ok": False,
                                 "msg": str(exc)}],
                    "log": [f"ERROR: {exc}"]}
        if parsed is None:
            return {"ok": True, "line": line, "results": [], "log": []}
        key, raw = parsed
        try:
            action = validate(key, raw, self._catalog, lineno=lineno)
        except ValidationError as exc:
            log = ["ERROR: " + err for err in exc.errors]
            log.append(f"stopped at line {lineno}")
            return {"ok": False, "line": line,
                    "results": [{"key": key, "line": lineno, "ok": False,
                                 "msg": "; ".join(exc.errors)}],
                    "log": log}
        log = ["warn: " + warn for warn in action.warnings]
        ok, msg = self._executor.run(action)
        log.append(f"{'ok' if ok else 'FAIL'} [{key}] {msg}")
        if not ok:
            log.append(f"stopped at line {lineno}")
        return {"ok": ok, "line": line,
                "results": [{"key": key, "line": lineno, "ok": ok,
                             "msg": msg}],
                "log": log}

    # -- reasoner (in-GUI observe -> plan -> act -> verify loop) ---------
    def _on_reason(self):
        if self._reason_session is not None:
            self._log("ERROR: reasoner already running (Stop first)")
            return
        task = self._task.model.get_value_as_string().strip()
        if not task:
            self._log("ERROR: type a Reasoner task first")
            return
        if not self._catalog:
            self._log("ERROR: no catalog loaded, cannot plan")
            return
        self._reason_session = ReasonerSession(
            task=task, max_steps=MAX_STEPS_DEFAULT)
        self._reason_stop = False
        self._log(f"--- reasoner: {task} (max {MAX_STEPS_DEFAULT} steps) ---")
        self._reason_observe()

    def _on_reason_stop(self):
        if self._reason_session is None:
            self._log("reasoner: not running")
            return
        self._reason_stop = True
        self._log("reasoner: stopping after this step...")

    def _reason_observe(self):
        """Fresh screenshot, then the plan+run step (or at once)."""
        target = next_capture_path(prefix="reason")
        started, msg = capture_viewport(
            target, on_done=self._on_reason_shot_done)
        self._log(("shot: " if started else "shot ERROR: ") + msg)
        if started:
            self._reason_pending_shot = str(target)
        else:
            self._reason_pending_shot = None
            self._reason_step()

    def _on_reason_shot_done(self, ok: bool, msg: str):
        self._log(("shot: " if ok else "shot ERROR: ") + msg)
        if ok and self._reason_pending_shot:
            self._last_shot = self._reason_pending_shot
        self._reason_pending_shot = None
        self._reason_step()

    def _reason_step(self):
        session = self._reason_session
        if session is None:
            return
        if self._reason_stop:
            self._reason_finish("stopped", "stopped by user")
            return
        step_no = len(session.steps) + 1
        self._thinker_config = load_config()  # re-read: no restart needed
        signatures = [
            help_line(key, self._catalog[key])
            for key in HANDLED_ACTIONS
            if key in self._catalog
        ]
        skills = select_skills(session.task, self._routing)
        snapshot = self._executor.snapshot()
        images = [self._last_shot] if self._last_shot else []
        if self._last_shot:
            snapshot += f"\nscreenshot: {self._last_shot}"
        # Reflex only on step 1 with the plain task: later steps carry
        # loop history that must never re-trigger a fixed plan.
        reflex_hit = (try_reflex(session.task, snapshot)
                      if step_no == 1 else None)
        if reflex_hit is not None:
            actions_text, reflex_notes = reflex_hit
            result = ThinkerPlan(actions_text=actions_text,
                                 notes=reflex_notes, skills=[],
                                 backend="reflex")
        else:
            result = thinker_plan(
                build_step_task(session),
                snapshot,
                signatures,
                skills,
                known_keys=set(self._catalog),
                config=self._thinker_config,
                images=images,
                loop=True,
                guided_regex=load_guided_regex(),
            )
        self._thinker_status.text = (
            f"Reasoner: step {step_no}/{session.max_steps} "
            f"({result.backend})"
        )
        self._log(f"--- reason step {step_no} ({result.backend}) ---")
        for note in result.notes:
            self._log("thinker: " + note)
        backend_block = check_backend(step_no, result.backend)
        if backend_block is not None:
            self._reason_finish("failed", backend_block)
            return
        done, runnable = split_verdict(result.actions_text)
        _log_trace({
            "event": "think",
            "reason_step": step_no,
            "task": session.task,
            "backend": result.backend,
            "skills": [str(s.get("skill") or s.get("name")) for s in skills],
            "images": images,
            "snapshot": snapshot,
            "actions": result.actions_text,
            "notes": result.notes,
        })
        if done:
            ignored = [ln for ln in runnable.splitlines() if ln.strip()]
            if ignored:
                self._log(f"reasoner: DONE verdict; "
                          f"ignored {len(ignored)} co-emitted line(s)")
            self._reason_finish("done", "planner verdict DONE")
            return
        try:
            batch = parse_batch(runnable)
        except ProtocolError as exc:
            self._reason_finish(
                "failed", f"planner emitted invalid lines: {exc}")
            return
        if not batch:
            status, reason = decide_empty_plan(session)
            self._reason_finish(status, reason)
            return
        self._prompt.model.set_value(runnable)
        outcome = self._run_batch_text(runnable)
        for line in outcome["log"]:
            self._log(line)
        _log_trace({
            "event": "run",
            "reason_step": step_no,
            "lines": outcome["lines"],
            "results": outcome["results"],
        })
        session.record(StepRecord(
            step=step_no, actions_text=runnable, backend=result.backend,
            results=outcome["results"], ok=bool(outcome["ok"])))
        decision, reason = decide_after_run(session, result.backend)
        if decision == "continue":
            self._log(f"reasoner: {reason} "
                      f"(step {step_no}/{session.max_steps})")
            self._reason_observe()
        else:
            self._reason_finish(decision, reason)

    def _reason_finish(self, status: str, reason: str):
        session = self._reason_session
        task = session.task if session is not None else ""
        ran = len(session.steps) if session is not None else 0
        if session is not None:
            session.status, session.reason = status, reason
        self._reason_session = None
        self._reason_stop = False
        self._thinker_status.text = (
            "Thinker: " + self._thinker_config.describe())
        self._log(f"--- reasoner {status} ({ran} step(s)): {reason} ---")
        _log_trace({
            "event": "reason_done",
            "task": task,
            "status": status,
            "reason": reason,
            "steps": ran,
        })

    # -- run -------------------------------------------------------------
    def _sense_capture(self):
        """One watchdog snapshot, or None. Never breaks the batch."""
        try:
            return capture_compact()
        except Exception:
            return None

    def _run_dispatch_text(self, text: str, task: str) -> dict:
        """Run a dispatch block: agents plan, the verdict gates execution.

        On supervisor failure nothing executes. On success the emitted
        action lines run through the normal batch path, so validation,
        execution, watchdog events, and bridge recording all behave
        alike. Recursion is one level: final_text holds validated
        dotted action keys only, never dispatch verbs.
        """
        sense_before = self._sense_capture()
        self._thinker_config = load_config()  # re-read: no restart needed
        deps = types.SimpleNamespace(
            thinker=thinker_mod, protocol=protocol_mod,
            dispatcher=dispatcher_mod, catalog=self._catalog,
            routing=self._routing,
            signatures=[help_line(k, self._catalog[k])
                        for k in HANDLED_ACTIONS if k in self._catalog])
        res = supervisor_mod.run_block(
            text, task or supervisor_mod.task_from_comments(text),
            self._executor.snapshot(), deps, config=self._thinker_config,
            guided_regex=load_guided_regex())
        if not res["ok"]:
            outcome = supervisor_mod.failure_outcome(text, res)
        else:
            outcome = supervisor_mod.combine_outcome(
                res, self._run_batch_text(res["final_text"]))
        try:
            events = self._watcher.observe_after(
                sense_before, self._sense_capture())
        except Exception:
            events = []
        for ev in events:
            outcome["log"].append("sense: " + ev)
        outcome["events"] = events
        return outcome

    def _run_batch_text(self, text: str, task: str = "") -> dict:
        """Validate + run one batch -> {"ok", "lines", "results", "log", "events"}.

        Shared by the Run button and the file bridge so both behave alike:
        top to bottom, stopping at the first failure. Batches opening a
        dispatch verb (DEPLOY/STEP/PARALLEL/COWORK) run the supervisor:
        agents plan, the verdict gates execution, and the emitted lines
        run through this same path. `task` feeds the agents' prompts
        (the Run button passes the task box; the bridge falls back to
        the first # comment). The sense watchdog snapshots the stage
        before/after so every executed batch reports what actually
        changed ("events", also mirrored into "log" as sense: lines).
        """
        if supervisor_mod.is_dispatch_text(text):
            return self._run_dispatch_text(text, task)
        try:
            batch = parse_batch(text)
        except ProtocolError as exc:
            return {"ok": False, "lines": [],
                    "results": [{"key": "", "line": 0, "ok": False,
                                 "msg": str(exc)}],
                    "log": [f"ERROR: {exc}"], "events": []}
        if not batch:
            return {"ok": True, "lines": [], "results": [],
                    "log": ["(nothing to run)"], "events": []}
        lines = [key + "".join(f" {k}={v}" for k, v in raw.items())
                 for key, raw, _ in batch]
        results, log = [], []
        ok_all = True
        sense_before = self._sense_capture()
        for key, raw, lineno in batch:
            try:
                action = validate(key, raw, self._catalog, lineno=lineno)
            except ValidationError as exc:
                for err in exc.errors:
                    log.append("ERROR: " + err)
                log.append(f"stopped at line {lineno}")
                results.append({"key": key, "line": lineno, "ok": False,
                                "msg": "; ".join(exc.errors)})
                ok_all = False
                break
            for warn in action.warnings:
                log.append("warn: " + warn)
            ok, msg = self._executor.run(action)
            log.append(f"{'ok' if ok else 'FAIL'} [{key}] {msg}")
            results.append({"key": key, "line": lineno, "ok": ok, "msg": msg})
            if not ok:
                log.append(f"stopped at line {lineno}")
                ok_all = False
                break
        try:
            events = self._watcher.observe_after(
                sense_before, self._sense_capture())
        except Exception:
            events = []
        for ev in events:
            log.append("sense: " + ev)
        return {"ok": ok_all, "lines": lines, "results": results,
                "log": log, "events": events}

    def _on_run(self):
        if not self._catalog:
            self._log("ERROR: no catalog loaded, cannot validate")
            return
        outcome = self._run_batch_text(
            self._prompt.model.get_value_as_string(),
            self._task.model.get_value_as_string().strip())
        for line in outcome["log"]:
            self._log(line)
        _log_trace({
            "event": "run",
            "lines": outcome["lines"],
            "results": outcome["results"],
            "events": outcome.get("events", []),
        })

    # -- timeline watcher (who pauses/stops the sim, and when) -----------
    def _tl_write(self, msg: str):
        """Append one timestamped line to the bridge timeline log."""
        try:
            path = default_bridge_dir() / "timeline.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            stamp = datetime.datetime.now().isoformat(timespec="milliseconds")
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"{stamp} {msg}\n")
        except Exception:
            pass

    def _watch_timeline(self):
        try:
            stream = omni.timeline.get_timeline_interface().get_timeline_event_stream()
        except Exception as exc:
            self._log(f"timeline watch: unavailable ({exc})")
            return
        for etype in ("PLAY", "PAUSE", "STOP"):
            try:
                sub = stream.create_subscription_to_pop_by_type(
                    getattr(omni.timeline.TimelineEventType, etype),
                    lambda _event, _kind=etype: self._on_timeline_event(_kind),
                )
            except Exception as exc:
                self._log(f"timeline watch: no {etype} subscription ({exc})")
                continue
            self._timeline_subs.append(sub)

    def _on_timeline_event(self, kind: str):
        try:
            current = omni.timeline.get_timeline_interface().get_current_time()
            msg = f"timeline {kind} t={current:.2f}"
        except Exception:
            msg = f"timeline {kind}"
        self._log("bridge: " + msg)
        self._tl_write(msg)

    # -- bridge (outside driver) -----------------------------------------
    def _on_bridge_toggle(self):
        if self._bridge_on:
            self._bridge_on = False
            self._bridge_btn.text = "Bridge: Start"
            self._bridge_status.text = "Bridge: off"
            if self._bridge_dirs is not None:
                try:
                    prev = read_status(self._bridge_dirs["base"])
                    write_status(self._bridge_dirs["base"], bridge="off",
                                 pending=0, last_cmd=prev.get("last_cmd"),
                                 last_ok=prev.get("last_ok"))
                except Exception:
                    pass
            self._log("bridge: off")
            return
        if not self._catalog:
            self._log("ERROR: no catalog loaded, bridge cannot validate")
            return
        try:
            self._bridge_dirs = ensure_layout()
        except OSError as exc:
            self._log(f"bridge ERROR: cannot create bridge folders: {exc}")
            return
        self._bridge_on = True
        self._bridge_btn.text = "Bridge: Stop"
        self._bridge_status.text = f"Bridge: on ({self._bridge_dirs['base']})"
        try:
            (self._bridge_dirs["base"] / "timeline.log").write_text(
                "", encoding="utf-8")
        except Exception:
            pass
        self._tl_write("bridge on")
        self._log(f"bridge: on, watching {self._bridge_dirs['inbox']}")
        self._log("bridge: drop a *.txt batch in inbox; results land in outbox/")
        try:
            asyncio.ensure_future(self._bridge_loop())
        except RuntimeError as exc:
            self._bridge_on = False
            self._bridge_btn.text = "Bridge: Start"
            self._bridge_status.text = "Bridge: off"
            self._log(f"bridge ERROR: no event loop to poll on: {exc}")

    async def _bridge_loop(self):
        while self._bridge_on:
            try:
                self._bridge_poll()
            except Exception as exc:  # never let one poll kill the loop
                self._log(f"bridge ERROR: {exc}")
            await asyncio.sleep(BRIDGE_POLL_SECONDS)

    def _bridge_poll(self):
        if not self._bridge_on or self._bridge_dirs is None:
            return
        if not self._catalog:
            return
        processed = process_inbox(
            self._bridge_dirs["base"],
            self._run_batch_text,
            snapshot_fn=self._executor.snapshot,
            log_fn=self._log,
        )
        for result in processed:
            self._tl_write(f"batch {result['cmd']} -> "
                           f"{'ok' if result['ok'] else 'FAIL'}")
            for line in result["log"]:
                self._log(line)
            _log_trace({
                "event": "bridge_run",
                "cmd": result["cmd"],
                "lines": result["lines"],
                "results": result["results"],
                "events": result.get("events", []),
            })
            png = self._bridge_dirs["outbox"] / (result["stem"] + ".png")
            started, msg = capture_viewport(
                png,
                on_done=lambda ok, m, rf=result["result_file"],
                p=str(png): self._on_bridge_shot_done(ok, m, rf, p),
            )
            self._log(("bridge shot: " if started else "bridge shot ERROR: ") + msg)
        if processed:
            self._bridge_status.text = (
                f"Bridge: on ({len(processed)} ran, last: {processed[-1]['cmd']})"
            )
        else:
            self._sense_idle_tick()

    def _sense_idle_tick(self):
        """Watchdog idle tick: report external stage edits, else stay quiet."""
        try:
            snap = self._sense_capture()
            if snap is None:
                return
            events = self._watcher.observe(snap)
        except Exception:
            return
        for ev in events:
            self._log("sense: " + ev)
            self._tl_write("sense " + ev)
        if events:
            _log_trace({"event": "sense", "events": events})

    def _on_bridge_shot_done(self, ok: bool, msg: str, result_file: str, png: str):
        self._log(("bridge shot: " if ok else "bridge shot ERROR: ") + msg)
        self._tl_write(f"shot {'ok' if ok else 'FAIL'} {Path(png).name}")
        if not update_result_shot(result_file, png, ok):
            self._log(f"bridge shot ERROR: cannot update {result_file}")

    def destroy(self):
        """Stop background work. Called on extension shutdown."""
        self._bridge_on = False
        self._reason_stop = True
        self._reason_session = None
        self._stream_stop.set()
        for sub in getattr(self, "_timeline_subs", []):
            try:
                sub.unsubscribe()
            except Exception:
                pass
        self._timeline_subs = []
        if self._bridge_dirs is not None:
            try:
                prev = read_status(self._bridge_dirs["base"])
                write_status(self._bridge_dirs["base"], bridge="off",
                             pending=0, last_cmd=prev.get("last_cmd"),
                             last_ok=prev.get("last_ok"))
            except Exception:
                pass
        self._bridge_dirs = None
