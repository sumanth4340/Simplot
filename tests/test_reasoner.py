"""Offline tests for the in-GUI Reasoner loop. Run: python tests/test_reasoner.py"""
import importlib.util
import json
import sys
import urllib.request as _urlmod
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"arreason_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


reasoner = _load("reasoner")
thinker = _load("thinker")
protocol = _load("protocol")
handlers = _load("handlers")  # must import with guarded Isaac deps
catalog = protocol.load_catalog(ROOT / "actions_compact.json")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _ok_results(*keys):
    return [{"key": k, "line": i + 1, "ok": True, "msg": "created"}
            for i, k in enumerate(keys)]


def _fail_results():
    return [
        {"key": "create.objects.plane", "line": 1, "ok": True, "msg": "created"},
        {"key": "joint.create.joint", "line": 2, "ok": False,
         "msg": "target not found: wheel_l"},
    ]


def _session(task="make a moon rover", max_steps=3):
    return reasoner.ReasonerSession(task=task, max_steps=max_steps)


# -- verdict parsing -----------------------------------------------------

def test_verdict_done_alone():
    done, runnable = reasoner.split_verdict("DONE\n")
    assert done is True and runnable.strip() == "", (done, runnable)


def test_verdict_done_case_and_space_insensitive():
    done, runnable = reasoner.split_verdict("  done  \n# all set\n")
    assert done is True, runnable
    assert "done" not in runnable.lower().replace("all set", ""), runnable


def test_verdict_done_wins_over_actions():
    done, runnable = reasoner.split_verdict("DONE\ncreate.objects.plane size=20\n")
    assert done is True, runnable
    # Kept for the log note; the GUI ignores runnable lines on DONE.
    assert "create.objects.plane" in runnable, runnable


def test_verdict_no_done_keeps_plan():
    text = "create.objects.plane size=20\nsim.play\n"
    done, runnable = reasoner.split_verdict(text)
    assert done is False and runnable == text, (done, runnable)


def test_verdict_done_prefix_is_not_done():
    done, _ = reasoner.split_verdict("DONEZO x=1\ncreate.objects.plane size=20\n")
    assert done is False, done


# -- retry task building --------------------------------------------------

def test_step_task_first_step_is_plain_task():
    session = _session()
    assert reasoner.build_step_task(session) == "make a moon rover"


def test_step_task_later_steps_carry_history():
    session = _session()
    session.record(reasoner.StepRecord(
        step=1, actions_text="create.objects.plane size=20",
        backend="glimmer", results=_fail_results(), ok=False))
    text = reasoner.build_step_task(session)
    assert text.startswith("make a moon rover"), text
    assert "Step 1" in text and "FAIL" in text, text
    assert "wheel_l" in text, text  # failure detail survives
    assert "DONE" in text, text  # model is told how to finish


# -- session bookkeeping ---------------------------------------------------

def test_session_last_ok_and_failures():
    session = _session()
    assert session.last_ok() is None
    assert session.failures() == []
    session.record(reasoner.StepRecord(
        step=1, actions_text="a", backend="glimmer",
        results=_fail_results(), ok=False))
    assert session.last_ok() is False
    fails = session.failures()
    assert len(fails) == 1 and "wheel_l" in fails[0], fails
    session.record(reasoner.StepRecord(
        step=2, actions_text="b", backend="glimmer",
        results=_ok_results("sim.play"), ok=True))
    assert session.last_ok() is True
    assert session.failures() == []  # failures() reports the latest step


# -- stop decisions --------------------------------------------------------

def test_empty_plan_fresh_session_fails():
    status, reason = reasoner.decide_empty_plan(_session())
    assert status == "failed" and "no action" in reason, (status, reason)


def test_empty_plan_after_clean_run_is_done():
    session = _session()
    session.record(reasoner.StepRecord(
        step=1, actions_text="a", backend="glimmer",
        results=_ok_results("sim.play"), ok=True))
    status, _ = reasoner.decide_empty_plan(session)
    assert status == "done", status


def test_empty_plan_after_failed_run_fails():
    session = _session()
    session.record(reasoner.StepRecord(
        step=1, actions_text="a", backend="glimmer",
        results=_fail_results(), ok=False))
    status, _ = reasoner.decide_empty_plan(session)
    assert status == "failed", status


def test_mock_is_single_pass():
    for ok, want in ((True, "done"), (False, "failed")):
        session = _session()
        session.record(reasoner.StepRecord(
            step=1, actions_text="a", backend="mock",
            results=_ok_results("sim.play") if ok else _fail_results(),
            ok=ok))
        decision, reason = reasoner.decide_after_run(session, "mock")
        assert decision == want, (ok, decision, reason)
        assert "mock" in reason, reason


def test_glimmer_loops_until_budget():
    session = _session(max_steps=3)
    session.record(reasoner.StepRecord(
        step=1, actions_text="a", backend="glimmer",
        results=_ok_results("sim.play"), ok=True))
    decision, _ = reasoner.decide_after_run(session, "glimmer")
    assert decision == "continue", decision  # verification pass, not done yet
    session.record(reasoner.StepRecord(
        step=2, actions_text="b", backend="glimmer",
        results=_fail_results(), ok=False))
    decision, _ = reasoner.decide_after_run(session, "glimmer")
    assert decision == "continue", decision  # repair pass after failure
    session.record(reasoner.StepRecord(
        step=3, actions_text="c", backend="glimmer",
        results=_fail_results(), ok=False))
    decision, reason = reasoner.decide_after_run(session, "glimmer")
    assert decision == "failed" and "budget" in reason, (decision, reason)


def test_glimmer_budget_with_clean_last_run_is_done():
    session = _session(max_steps=2)
    for i in (1, 2):
        session.record(reasoner.StepRecord(
            step=i, actions_text="x", backend="glimmer",
            results=_ok_results("sim.play"), ok=True))
    decision, reason = reasoner.decide_after_run(session, "glimmer")
    assert decision == "done", (decision, reason)


def test_mock_cannot_continue_a_loop():
    assert reasoner.check_backend(step_no=1, backend="mock") is None
    assert reasoner.check_backend(step_no=1, backend="glimmer") is None
    reason = reasoner.check_backend(step_no=2, backend="mock")
    assert reason and "mock" in reason, reason
    assert reasoner.check_backend(step_no=2, backend="glimmer") is None


# -- loop prompt threading ---------------------------------------------------

def test_loop_system_prompt_adds_done_rule():
    prompt = thinker.build_system_prompt(["sim.play"], [], loop=True)
    assert "DONE" in prompt, prompt
    assert "Never repeat actions that already succeeded" in prompt, prompt


def test_single_shot_prompt_unchanged():
    prompt = thinker.build_system_prompt(["sim.play"], [])
    assert "DONE" not in prompt, prompt
    assert "ONLY action lines" in prompt, prompt


def _plan_with_stubbed_reply(content, **plan_kw):
    """Run thinker.plan against a stubbed endpoint; return (result, sent)."""
    sent = {}
    payload = {"choices": [{"message": {"content": content}}]}

    class _Resp:
        def read(self):
            return json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    real_urlopen = _urlmod.urlopen

    def fake_urlopen(request, timeout=None):
        body = json.loads(request.data.decode("utf-8"))
        sent["system"] = body["messages"][0]["content"]
        return _Resp()

    _urlmod.urlopen = fake_urlopen
    try:
        cfg = thinker.ThinkerConfig(
            endpoint="https://x.modal.run/v1/chat/completions", api_key="k")
        result = thinker.plan("play", "", ["sim.play"], [], set(catalog),
                              config=cfg, **plan_kw)
    finally:
        _urlmod.urlopen = real_urlopen
    return result, sent


def test_plan_loop_threads_loop_prompt():
    result, sent = _plan_with_stubbed_reply("sim.play\n", loop=True)
    assert "DONE" in sent["system"], sent["system"][-500:]
    assert result.backend == "glimmer", result.backend
    assert result.actions_text.splitlines() == ["sim.play"], result.actions_text


def test_plan_loop_done_verdict_finishes():
    result, _ = _plan_with_stubbed_reply(
        "All placed, nothing left.\nDONE\n", loop=True)
    assert result.backend == "glimmer", result.backend
    assert result.actions_text == "DONE\n", result.actions_text
    assert any("verdict" in n for n in result.notes), result.notes
    done, _ = reasoner.split_verdict(result.actions_text)
    assert done is True


def test_plan_loop_done_wins_over_actions():
    result, _ = _plan_with_stubbed_reply(
        "DONE\ncreate.objects.plane size=20\n", loop=True)
    assert result.backend == "glimmer", result.backend
    assert result.actions_text == "DONE\n", result.actions_text


def test_plan_single_shot_ignores_done():
    # Single-shot Think never asks for DONE; the word stays dropped prose.
    result, _ = _plan_with_stubbed_reply("DONE\n")
    assert result.backend == "mock", result.backend


# -- scripted end-to-end loop --------------------------------------------------

def test_scripted_repair_loop_reaches_done():
    """Fail once, repair, then DONE: the policy walks the whole loop."""
    plans = [
        ("glimmer", "create.objects.plane size=20\n"),
        ("glimmer", "DONE\n"),
    ]
    outcomes = [
        [{"key": "create.objects.plane", "line": 1, "ok": False,
          "msg": "boom"}],
    ]
    session = _session(max_steps=4)
    step_no = 0
    for backend, text in plans:
        step_no += 1
        assert reasoner.check_backend(step_no, backend) is None
        done, runnable = reasoner.split_verdict(text)
        if done:
            session.status, session.reason = "done", "planner verdict DONE"
            break
        batch = protocol.parse_batch(runnable)
        assert batch, "loop step has no runnable actions"
        for key, raw, lineno in batch:
            protocol.validate(key, raw, catalog, lineno=lineno)
        results = outcomes.pop(0) if outcomes else _ok_results(
            *[k for k, _, _ in batch])
        ok = all(r["ok"] for r in results)
        session.record(reasoner.StepRecord(
            step=step_no, actions_text=runnable, backend=backend,
            results=results, ok=ok))
        decision, reason_text = reasoner.decide_after_run(session, backend)
        if decision != "continue":
            session.status, session.reason = decision, reason_text
            break
    else:
        raise AssertionError("loop never finished")
    assert session.status == "done", (session.status, session.reason)
    assert len(session.steps) == 1, len(session.steps)
    assert "Step 1" in reasoner.build_step_task(session)


def test_mock_plan_is_action_only_for_loop_step():
    """Whatever the loop runs must parse + validate as catalog actions."""
    text, _ = thinker.mock_plan("make a moon rover", "")
    done, runnable = reasoner.split_verdict(text)
    assert done is False
    batch = protocol.parse_batch(runnable)
    assert batch, "mock plan has no runnable lines"
    for key, raw, lineno in batch:
        assert key in set(handlers.HANDLED_ACTIONS), key
        protocol.validate(key, raw, catalog, lineno=lineno)


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
