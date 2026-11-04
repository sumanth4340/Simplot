"""Tests for the dispatcher grammar. Run: python tests/test_dispatch.py"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"ardisp_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


dispatcher = _load("dispatcher")
thinker = _load("thinker")
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _raises(text):
    try:
        dispatcher.validate_block(text)
    except dispatcher.DispatchError:
        return
    raise AssertionError(f"accepted invalid block:\n{text}")


def test_single_agent_ok():
    ops = dispatcher.validate_block(
        "DEPLOY agent=sense\n"
        "STEP n=1 agent=sense do=read-stage\n")
    assert [o["verb"] for o in ops] == ["DEPLOY", "STEP"]


def test_multi_agent_ok():
    ops = dispatcher.validate_block(
        "# rover drive plan\n"
        "DEPLOY agent=sense\n"
        "DEPLOY agent=articulation needs=physics\n"
        "DEPLOY agent=physics\n"
        "DEPLOY agent=rosnav needs=articulation+sensors\n"
        "DEPLOY agent=sensors\n"
        "DEPLOY agent=xval\n"
        "PARALLEL agents=sense+physics\n"
        "COWORK agents=articulation+rosnav\n"
        "STEP n=1 agent=sense do=read-stage\n"
        "STEP n=2 agent=articulation do=attach-wheels\n"
        "STEP n=3 agent=rosnav do=drive-forward\n")
    verbs = [o["verb"] for o in ops]
    assert verbs.count("DEPLOY") == 6 and verbs.count("STEP") == 3


def test_done_and_comments_kept():
    ops = dispatcher.validate_block("DEPLOY agent=stage\nDONE\n")
    assert [o["verb"] for o in ops] == ["DEPLOY", "DONE"]


def test_rejects_prose_and_bad_verbs():
    _raises("DEPLOY agent=sense\nI will now read the stage\n")
    _raises("SPAWN agent=sense\n")
    _raises("DEPLOY agent=sense\nstep n=1 agent=sense do=x\n")


def test_rejects_roster_violations():
    _raises("DEPLOY agent=hal\n")
    _raises("DEPLOY agent=sense\nDEPLOY agent=sense\n")
    _raises("DEPLOY agent=sense needs=sense\n")
    _raises("DEPLOY agent=sense\nSTEP n=1 agent=stage do=x\n")
    _raises("DEPLOY agent=sense\nDEPLOY agent=stage\n"
            "PARALLEL agents=sense+stage+hal\n")
    _raises("DEPLOY agent=sense\nCOWORK agents=sense+sense\n")


def test_rejects_bad_shape():
    _raises("DEPLOY agent =sense\n")
    _raises("DEPLOY agent=sense foo=1\n")
    _raises("DEPLOY agent=sense agent=stage\n")
    _raises("DEPLOY agent=sense\nSTEP n=1 agent=sense do=read the stage\n")
    _raises("DEPLOY agent=sense\nSTEP n=one agent=sense do=x\n")


def test_empty_plan_ok():
    assert dispatcher.validate_block("# only a comment\n") is not None
    assert [o["verb"] for o in dispatcher.validate_block("DONE\n")] == ["DONE"]
    assert dispatcher.validate_block("") == []


def test_rejects_unordered_steps():
    _raises("DEPLOY agent=sense\nSTEP n=2 agent=sense do=x\n")
    _raises("DEPLOY agent=sense\nSTEP n=1 agent=sense do=a\n"
            "STEP n=1 agent=sense do=b\n")
    _raises("DEPLOY agent=sense\nDEPLOY agent=stage\nDEPLOY agent=xval\n"
            "STEP n=1 agent=sense do=a\nSTEP n=3 agent=stage do=b\n")


def test_multi_agent_requires_xval():
    _raises("DEPLOY agent=sense\nDEPLOY agent=stage\n"
            "STEP n=1 agent=sense do=a\nSTEP n=2 agent=stage do=b\n")
    dispatcher.validate_block(  # single worker + xval is fine
        "DEPLOY agent=sense\nDEPLOY agent=xval\n"
        "STEP n=1 agent=sense do=a\n")


def test_roster_matches_agents_md():
    agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    table = re.findall(r"^\| `(\w+)` \|", agents_md, re.M)
    assert sorted(table) == sorted(dispatcher.ROSTER), (table, dispatcher.ROSTER)
    assert len(dispatcher.ROSTER) == 18


def test_agent_packs_exist():
    assert set(dispatcher.AGENT_PACKS) == set(dispatcher.ROSTER)
    for agent, pack in dispatcher.AGENT_PACKS.items():
        assert (ROOT / "skills" / pack).is_dir(), f"{agent} -> {pack}"
    assert len(dispatcher.describe_roster()) == 18


def test_is_dispatch_line():
    assert dispatcher.is_dispatch_line("DEPLOY agent=sense")
    assert dispatcher.is_dispatch_line("STEP n=1 agent=sense do=x")
    assert dispatcher.is_dispatch_line("DONE")
    assert dispatcher.is_dispatch_line("# note")
    assert not dispatcher.is_dispatch_line("create.objects.cuboid size=1")
    assert not dispatcher.is_dispatch_line("I will deploy sense now")
    assert not dispatcher.is_dispatch_line("")


def test_dispatch_prompt_builder():
    prompt = thinker.build_dispatch_prompt(dispatcher.describe_roster(), [])
    for verb in ("DEPLOY", "STEP", "PARALLEL", "COWORK"):
        assert verb in prompt, verb
    for agent in dispatcher.ROSTER:
        assert f"- {agent}:" in prompt, agent
    assert "xval" in prompt


def test_summarize_agents():
    text = ("DEPLOY agent=sense\n"
            "DEPLOY agent=rosnav needs=sense\n"
            "DEPLOY agent=xval\n"
            "STEP n=1 agent=sense do=read-stage\n"
            "STEP n=2 agent=rosnav do=drive-forward\n")
    assert dispatcher.summarize_agents(text) == (
        "sense[1:read-stage] + rosnav[2:drive-forward] + xval[verdict]")


def test_summarize_agents_empty_and_idle():
    assert dispatcher.summarize_agents("# only a comment\n") == (
        "no agents (empty plan)")
    assert dispatcher.summarize_agents("") == "no agents (empty plan)"
    assert dispatcher.summarize_agents("DEPLOY agent=sense\n") == (
        "sense[idle]")


def test_summarize_agents_never_raises():
    assert dispatcher.summarize_agents("SPAWN agent=sense\n") == ""
    assert dispatcher.summarize_agents("DEPLOY agent =sense\n") == ""
    long_text = "DEPLOY agent=sense\n" + "".join(
        f"STEP n={n} agent=sense do=job-{n:03d}-with-a-long-slug\n"
        for n in range(1, 30))
    short = dispatcher.summarize_agents(long_text, max_len=40)
    assert len(short) == 40 and short.endswith("\u2026")


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
