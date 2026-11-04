"""Offline tests for the Thinker client. Run: python tests/test_thinker.py"""
import base64
import importlib.util
import json
import os
import sys
import tempfile
import urllib.request as _urlmod
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"arthink_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker")
protocol = _load("protocol")
handlers = _load("handlers")  # must import with guarded Isaac deps
dispatcher = _load("dispatcher")
catalog = protocol.load_catalog(ROOT / "actions_compact.json")
routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _assert_mock_validates(task, snapshot=""):
    text, notes = thinker.mock_plan(task, snapshot)
    assert text.strip(), "mock plan is empty"
    assert notes, "mock plan has no notes"
    batch = protocol.parse_batch(text)
    assert batch, "mock plan has no parseable lines"
    for key, raw, lineno in batch:
        assert key in set(handlers.HANDLED_ACTIONS), f"mock emits unhandled {key}"
        protocol.validate(key, raw, catalog, lineno=lineno)
    return text


def test_extract_strips_fences_and_prose():
    raw = (
        "Sure, here is your scene:\n"
        "```\n"
        "create.objects.plane size=20\n"
        "1. create.objects.cuboid size=1 pos=0,0,2\n"
        "```\n"
        "Let me know if you want more."
    )
    text, notes = thinker.extract_actions(raw, set(catalog))
    assert text.splitlines() == [
        "create.objects.plane size=20",
        "create.objects.cuboid size=1 pos=0,0,2",
    ], text
    assert notes and "prose" in notes[0], notes


def test_extract_unknown_key_flagged_as_draft():
    text, _ = thinker.extract_actions("create.objects.teleporter x=1", set(catalog))
    assert text.startswith("# DRAFT"), text


def test_select_skills_finds_relevant():
    names = [s["skill"] for s in thinker.select_skills(
        "convert my URDF robot to USD and import it", routing)]
    assert "urdf-mjcf-to-usd-conversion" in names, names
    names = [s["skill"] for s in thinker.select_skills(
        "navigate the robot with ROS2 Nav2", routing)]
    assert "isaac-sim-ros2-bridge" in names or "isaac-sim-robot-navigation" in names, names


def test_select_skills_empty_task():
    assert thinker.select_skills("", routing) == []
    assert thinker.select_skills("make a cube", []) == []


def test_mock_rover_plan_validates():
    text = _assert_mock_validates("make a moon rover with two wheels and drive it")
    assert "joint.create.joint" in text and "robot.add.articulation" in text
    assert text.splitlines()[-1] == "sim.play", text


def test_mock_drive_sets_target_velocity():
    text = _assert_mock_validates("build a robot car and drive it")
    assert text.count("target_velocity=5") == 2, text
    text = _assert_mock_validates("make a moon rover")
    assert "target_velocity" not in text, text


def test_mock_cube_plan_validates():
    text = _assert_mock_validates("create a red cube")
    assert "create.objects.cuboid" in text


def test_mock_default_scene_validates():
    _assert_mock_validates("hello there")


def test_mock_skips_plane_when_present():
    text = _assert_mock_validates(
        "make a cube", snapshot="sim: paused\n[RC-] /World/GroundPlane (Plane)")
    assert "create.objects.plane" not in text, text


def test_mock_color_parsed():
    text = _assert_mock_validates("create a red cube")
    assert "color=1,0,0" in text, text
    text = _assert_mock_validates("make a green ball")
    assert "color=0.2,0.8,0.2" in text, text


def test_mock_count_spreads_instances():
    text = _assert_mock_validates("make three spheres")
    lines = [ln for ln in text.splitlines()
             if ln.startswith("create.objects.sphere")]
    assert len(lines) == 3, text
    assert len({ln.split("pos=")[1].split()[0] for ln in lines}) == 3, text


def test_mock_size_adjective_scales():
    text = _assert_mock_validates("build a huge green cylinder")
    assert "radius=1" in text and "height=2.5" in text, text
    assert "color=0.2,0.8,0.2" in text, text
    text = _assert_mock_validates("drop a tiny cube")
    assert "size=0.5" in text, text


def test_mock_tower_stacks_vertically():
    text = _assert_mock_validates("stack two boxes")
    lines = [ln for ln in text.splitlines()
             if ln.startswith("create.objects.cuboid")]
    assert len(lines) == 2, text
    poss = [[float(v) for v in ln.split("pos=")[1].split()[0].split(",")]
            for ln in lines]
    assert poss[0][0] == poss[1][0], poss  # same column
    assert poss[1][2] > poss[0][2] + 0.9, poss  # stacked, not intersecting


def test_mock_clauses_pair_colors():
    text = _assert_mock_validates("red cube and blue sphere")
    cuboid = next(ln for ln in text.splitlines()
                  if ln.startswith("create.objects.cuboid"))
    sphere = next(ln for ln in text.splitlines()
                  if ln.startswith("create.objects.sphere"))
    assert "color=1,0,0" in cuboid, text
    assert "color=0.2,0.4,0.9" in sphere, text


def test_mock_heavy_targets_named_body():
    text = _assert_mock_validates("drop a heavy box on the ground")
    assert "name=heavy_cube" in text, text
    assert "physics.set.mass target=heavy_cube value=5" in text, text


def test_mock_play_alone_runs_no_demo():
    for task in ("play", "run the simulation"):
        text, _ = thinker.mock_plan(task, "")
        assert text.splitlines() == ["sim.play"], (task, text)


def test_mock_digits_and_cap():
    text = _assert_mock_validates("make 2 cubes")
    assert sum(1 for ln in text.splitlines()
              if ln.startswith("create.objects.cuboid")) == 2, text
    text, notes = thinker.mock_plan("make 10 cubes", "")
    assert sum(1 for ln in text.splitlines()
              if ln.startswith("create.objects.cuboid")) == 6, text
    assert any("cap" in n for n in notes), notes


def test_mock_explicit_plane_skipped_is_noop():
    text, notes = thinker.mock_plan(
        "add a ground plane",
        snapshot="sim: paused\n[RC-] /World/GroundPlane (Plane)")
    assert text.strip() == "", text
    assert any("plane" in n for n in notes), notes


def test_mock_parametric_geometry_has_no_overlaps():
    # Same penetration-free contract as the fixed plans, for parsed plans.
    for task in ("make three spheres", "stack two boxes",
                 "build a huge green cylinder", "red cube and blue sphere",
                 "drop a heavy box", "create 4 capsules in a tower",
                 "two tiny cubes and a giant ball"):
        text, _ = thinker.mock_plan(task)
        boxes, spheres = [], []
        for key, raw, lineno in protocol.parse_batch(text):
            params = protocol.validate(key, raw, catalog, lineno=lineno).params
            if key == "create.objects.cuboid":
                boxes.append(([float(v) for v in params["pos"]],
                              float(params["size"]) / 2))
            elif key == "create.objects.sphere":
                spheres.append(([float(v) for v in params["pos"]],
                                float(params["radius"])))
            elif key in ("create.objects.cylinder", "create.objects.cone",
                         "create.objects.capsule"):
                spheres.append(([float(v) for v in params["pos"]],
                                max(float(params["height"]) / 2,
                                    float(params["radius"]))))
        assert boxes or spheres, f"no bodies in mock plan for {task!r}"
        for center, half in boxes:
            assert center[2] - half > 0, f"box sunk into ground: {task}"
        for center, radius in spheres:
            assert center[2] - radius >= -1e-6, f"sphere sunk: {task}"
            for bcenter, half in boxes:
                closest = [min(max(center[i], bcenter[i] - half),
                               bcenter[i] + half) for i in range(3)]
                dist = sum((center[i] - closest[i]) ** 2
                           for i in range(3)) ** 0.5
                assert dist >= radius - 1e-6, f"sphere in box: {task}"
        for i in range(len(spheres)):
            for j in range(i + 1, len(spheres)):
                dist = sum((spheres[i][0][k] - spheres[j][0][k]) ** 2
                           for k in range(3)) ** 0.5
                assert dist >= spheres[i][1] + spheres[j][1] - 1e-6, \
                    f"spheres overlap: {task}"


def test_mock_geometry_has_no_overlaps():
    # Regression: wheels once spawned inside the chassis and PhysX ejected
    # one on play. Every pair of mock-created bodies must be
    # penetration-free and rest on or above the ground.
    for task in ("make a moon rover", "hello there", "create a red cube",
                 "create a cylinder and a cone", "drop a capsule"):
        text, _ = thinker.mock_plan(task)
        boxes, spheres = [], []
        for key, raw, lineno in protocol.parse_batch(text):
            params = protocol.validate(key, raw, catalog, lineno=lineno).params
            if key == "create.objects.cuboid":
                boxes.append(([float(v) for v in params["pos"]],
                              float(params["size"]) / 2))
            elif key == "create.objects.sphere":
                spheres.append(([float(v) for v in params["pos"]],
                                float(params["radius"])))
            elif key in ("create.objects.cylinder", "create.objects.cone",
                         "create.objects.capsule"):
                spheres.append(([float(v) for v in params["pos"]],
                                max(float(params["height"]) / 2,
                                    float(params["radius"]))))
        assert boxes or spheres, f"no bodies in mock plan for {task!r}"
        for center, half in boxes:
            assert center[2] - half > 0, f"box sunk into ground: {task}"
        for center, radius in spheres:
            assert center[2] - radius >= -1e-6, f"sphere sunk: {task}"
            for bcenter, half in boxes:
                closest = [min(max(center[i], bcenter[i] - half),
                               bcenter[i] + half) for i in range(3)]
                dist = sum((center[i] - closest[i]) ** 2
                           for i in range(3)) ** 0.5
                assert dist >= radius - 1e-6, f"sphere in box: {task}"
        for i in range(len(spheres)):
            for j in range(i + 1, len(spheres)):
                dist = sum((spheres[i][0][k] - spheres[j][0][k]) ** 2
                           for k in range(3)) ** 0.5
                assert dist >= spheres[i][1] + spheres[j][1] - 1e-6, \
                    f"spheres overlap: {task}"


def test_plan_unconfigured_uses_mock():
    cfg = thinker.ThinkerConfig(endpoint="", api_key="")
    result = thinker.plan("make a rover", "", [], [], set(catalog), config=cfg)
    assert result.backend == "mock", result.backend
    assert "not configured" in " ".join(result.notes)
    batch = protocol.parse_batch(result.actions_text)
    assert batch, "fallback plan is empty"


def test_plan_endpoint_failure_falls_back():
    cfg = thinker.ThinkerConfig(endpoint="http://127.0.0.1:1/v1/chat/completions",
                                api_key="x", timeout=5)
    result = thinker.plan("make a cube", "", [], [], set(catalog), config=cfg)
    assert result.backend == "mock", result.backend
    assert any("failed" in n for n in result.notes), result.notes


def test_plan_live_endpoint_stubbed_transport():
    captured = {}
    payload = {"choices": [{"message": {"content": (
        "Here you go:\n"
        "```\ncreate.objects.plane size=20\nsim.play\n```\n")}}]}

    class _Resp:
        def read(self):
            return json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    real_urlopen = _urlmod.urlopen

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        body = json.loads(request.data.decode("utf-8"))
        captured["model"] = body["model"]
        captured["roles"] = [m["role"] for m in body["messages"]]
        return _Resp()

    _urlmod.urlopen = fake_urlopen
    try:
        cfg = thinker.ThinkerConfig(
            endpoint="https://x.modal.run/v1/chat/completions",
            api_key="test-key", timeout=10)
        result = thinker.plan("play the sim", "", ["sim.play"], [], set(catalog),
                              config=cfg)
    finally:
        _urlmod.urlopen = real_urlopen
    assert captured["url"] == "https://x.modal.run/v1/chat/completions", captured
    assert captured["auth"] == "Bearer test-key", captured
    assert captured["model"] == "glimmer-30b", captured
    assert captured["roles"] == ["system", "user"], captured
    assert captured["timeout"] == 10, captured
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert result.actions_text.splitlines() == [
        "create.objects.plane size=20", "sim.play"], result.actions_text
    assert result.raw, "raw reply not kept"


def test_system_prompt_lists_actions_and_skills():
    skills = thinker.select_skills("convert URDF robot to USD", routing, top_k=2)
    prompt = thinker.build_system_prompt(["sim.play", "sim.step [n]"], skills)
    assert "ONLY action lines" in prompt
    assert "- sim.play" in prompt
    assert "urdf-mjcf-to-usd-conversion" in prompt


# 1x1 transparent PNG
_PNG_1X1_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9Q"
    "DwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _temp_png():
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    Path(path).write_bytes(base64.b64decode(_PNG_1X1_B64))
    return path


def test_encode_image_data_url():
    path = _temp_png()
    try:
        url = thinker.encode_image(path)
    finally:
        os.unlink(path)
    assert url == "data:image/png;base64," + _PNG_1X1_B64, url[:60]


def test_encode_image_missing_raises():
    try:
        thinker.encode_image("Z:/does/not/exist.png")
    except thinker.ThinkerError as exc:
        assert "cannot read image" in str(exc), exc
        return
    raise AssertionError("expected ThinkerError")


def test_user_content_with_and_without_images():
    path = _temp_png()
    try:
        content, notes, used = thinker.build_user_content("do x", "snap", [path])
        assert isinstance(content, list), type(content)
        assert content[0] == {"type": "text",
                              "text": thinker.build_user_prompt("do x", "snap")}
        assert content[1]["type"] == "image_url", content[1]
        assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
        assert used == 1 and notes == [], (used, notes)
        content, _, used = thinker.build_user_content("do x", "snap", [path] * 5)
        assert used == thinker.MAX_IMAGES, used
        assert len(content) == 1 + thinker.MAX_IMAGES
        content, _, used = thinker.build_user_content("do x", "snap", [])
        assert isinstance(content, str) and used == 0
    finally:
        os.unlink(path)


def test_user_content_skips_unreadable_image():
    content, notes, used = thinker.build_user_content("do x", "", ["Z:/nope.png"])
    assert isinstance(content, str) and used == 0
    assert notes and "cannot read image" in notes[0], notes


def test_plan_sends_images_to_endpoint():
    captured = {}
    payload = {"choices": [{"message": {"content": "sim.play\n"}}]}

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
        captured["content"] = body["messages"][1]["content"]
        return _Resp()

    path = _temp_png()
    _urlmod.urlopen = fake_urlopen
    try:
        cfg = thinker.ThinkerConfig(
            endpoint="https://x.modal.run/v1/chat/completions", api_key="k")
        result = thinker.plan("play", "", [], [], set(catalog), config=cfg,
                              images=[path, "Z:/nope.png"])
    finally:
        _urlmod.urlopen = real_urlopen
        os.unlink(path)
    blocks = captured["content"]
    assert isinstance(blocks, list) and len(blocks) == 2, blocks
    assert blocks[1]["type"] == "image_url", blocks
    assert result.backend == "glimmer" and result.images == 1, result
    assert any("cannot read image" in n for n in result.notes), result.notes


def test_plan_mock_notes_images_ignored():
    cfg = thinker.ThinkerConfig(endpoint="", api_key="")
    result = thinker.plan("make a cube", "", [], [], set(catalog), config=cfg,
                          images=["shot.png"])
    assert result.backend == "mock" and result.images == 0, result
    assert any("text-only" in n for n in result.notes), result.notes


def test_endpoint_normalization():
    norm = thinker._normalize_endpoint
    assert norm("https://x.modal.run") == "https://x.modal.run/v1/chat/completions"
    assert norm("https://x.modal.run/") == "https://x.modal.run/v1/chat/completions"
    assert norm("https://x.modal.run/v1") == "https://x.modal.run/v1/chat/completions"
    full = "https://x.modal.run/v1/chat/completions"
    assert norm(full) == full
    assert norm("") == ""


def _sse_lines(pieces):
    lines = [("data: " + json.dumps(
        {"choices": [{"delta": {"content": piece}}]})).encode("utf-8")
        for piece in pieces]
    return lines + [b"data: [DONE]"]


class _StreamResp:
    """Stub SSE response: byte lines, served-count, optional mid-cut."""

    def __init__(self, lines, fail_after=None, exc=None):
        self._lines = list(lines)
        self._fail_after = fail_after
        self._exc = exc
        self.served = 0
        self.closed = False

    def __iter__(self):
        for line in self._lines:
            if (self._fail_after is not None
                    and self.served >= self._fail_after):
                raise self._exc
            self.served += 1
            yield line + b"\n"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True
        return False


def _stream_cfg():
    return thinker.ThinkerConfig(
        endpoint="https://x.modal.run/v1/chat/completions",
        api_key="test-key", timeout=10)


def test_stream_completion_yields_deltas_and_sets_stream_flag():
    captured = {}
    resp = _StreamResp(_sse_lines(
        ["create.ob", "jects.plane size=20\nsim", ".play\n"]))
    real_urlopen = _urlmod.urlopen

    def fake_urlopen(request, timeout=None):
        captured["timeout"] = timeout
        body = json.loads(request.data.decode("utf-8"))
        captured["stream"] = body.get("stream")
        captured["roles"] = [m["role"] for m in body["messages"]]
        return resp

    _urlmod.urlopen = fake_urlopen
    try:
        deltas = list(thinker.stream_completion(
            "https://x.modal.run/v1/chat/completions", "k", "m",
            [{"role": "user", "content": "hi"}], timeout=10))
    finally:
        _urlmod.urlopen = real_urlopen
    assert "".join(deltas) == "create.objects.plane size=20\nsim.play\n"
    assert captured["stream"] is True, captured
    assert captured["roles"] == ["system", "user"] or captured["roles"] == ["user"], captured
    assert captured["timeout"] == 10, captured
    assert resp.closed


def test_stream_completion_http_error_raises_thinker_error():
    import urllib.error
    real_urlopen = _urlmod.urlopen

    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 503, "busy", {}, None)

    _urlmod.urlopen = fake_urlopen
    try:
        try:
            list(thinker.stream_completion("https://x", "k", "m", []))
        except thinker.ThinkerError as exc:
            assert "503" in str(exc), exc
        else:
            raise AssertionError("HTTPError did not become ThinkerError")
    finally:
        _urlmod.urlopen = real_urlopen


def test_stream_extractor_matches_batch():
    known = set(catalog)
    battery = [
        "Here you go:\n```\ncreate.objects.plane size=20\nsim.play\n```\n",
        "# a comment\n\n1. create.objects.plane size=20\n- sim.play\n",
        "made.up.action x=1\ncreate.objects.plane size=20\nsome prose\n",
        "```\ncreate.objects.plane size=20\n",  # unclosed fence
        "DONE\ncreate.objects.plane size=20\n",  # no verdict: prose drop
    ]
    for text in battery:
        kept, notes = thinker.extract_actions(text, known)
        whole = thinker.StreamExtractor(known)
        items = whole.feed(text) + whole.flush()[0]
        assert [line for _, line in items] == kept.splitlines(), text
        assert whole.flush()[1] == notes, text
        charfed = thinker.StreamExtractor(known)
        fed = []
        for char in text:
            fed += charfed.feed(char)
        fed += charfed.flush()[0]
        assert [line for _, line in fed] == kept.splitlines(), text


def test_stream_extractor_done_verdict():
    known = set(catalog)
    verdict = thinker.StreamExtractor(known, verdict=True)
    items = verdict.feed("create.objects.plane size=20\nDONE\n")
    items += verdict.flush()[0]
    assert verdict.done is True
    assert [line for _, line in items] == ["create.objects.plane size=20"]
    plain = thinker.StreamExtractor(known)
    items = plain.feed("DONE\n") + plain.flush()[0]
    assert plain.done is False
    assert items == [], items  # batch parity: prose drop


def test_plan_stream_delivers_lines_live():
    resp = _StreamResp(_sse_lines(
        ["create.objects.plane", " size=20\nsim", ".play\n"]))
    seen = []
    real_urlopen = _urlmod.urlopen
    _urlmod.urlopen = lambda request, timeout=None: resp
    try:
        result = thinker.plan_stream(
            "play the sim", "", ["sim.play"], [], set(catalog),
            config=_stream_cfg(),
            on_line=lambda line, is_comment: seen.append(
                (line, is_comment)) or True)
    finally:
        _urlmod.urlopen = real_urlopen
    assert seen == [("create.objects.plane size=20", False),
                    ("sim.play", False)], seen
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert result.actions_text == ("create.objects.plane size=20\nsim.play")
    assert result.raw == "create.objects.plane size=20\nsim.play\n"


def test_plan_stream_sink_false_stops_early():
    resp = _StreamResp(_sse_lines(
        ["create.objects.plane size=20\n", "sim.play\n", "sim.stop\n"]))
    seen = []
    real_urlopen = _urlmod.urlopen
    _urlmod.urlopen = lambda request, timeout=None: resp
    try:
        def sink(line, is_comment):
            seen.append(line)
            return False  # stop after the first line

        result = thinker.plan_stream(
            "play", "", [], [], set(catalog), config=_stream_cfg(),
            on_line=sink)
    finally:
        _urlmod.urlopen = real_urlopen
    assert seen == ["create.objects.plane size=20"], seen
    assert resp.served < 4, resp.served  # never read the tail chunks
    assert resp.closed
    assert result.actions_text == "create.objects.plane size=20"


def test_plan_stream_unconfigured_uses_mock():
    seen = []
    cfg = thinker.ThinkerConfig(endpoint="", api_key="")
    result = thinker.plan_stream(
        "make a cube", "", [], [], set(catalog), config=cfg,
        on_line=lambda line, is_comment: seen.append(line) or True)
    assert result.backend == "mock", (result.backend, result.notes)
    assert seen, "mock lines never reached the sink"
    assert any("not configured" in n for n in result.notes), result.notes


def test_plan_stream_midstream_break_keeps_partial():
    import urllib.error
    resp = _StreamResp(
        _sse_lines(["create.objects.plane size=20\n", "sim.pl"]),
        fail_after=1, exc=urllib.error.URLError("boom"))
    seen = []
    real_urlopen = _urlmod.urlopen
    _urlmod.urlopen = lambda request, timeout=None: resp
    try:
        result = thinker.plan_stream(
            "play", "", [], [], set(catalog), config=_stream_cfg(),
            on_line=lambda line, is_comment: seen.append(line) or True)
    finally:
        _urlmod.urlopen = real_urlopen
    assert seen == ["create.objects.plane size=20"], seen
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert any("kept 1 line" in n for n in result.notes), result.notes


def test_plan_stream_prose_only_falls_back_to_mock():
    resp = _StreamResp(_sse_lines(["Sure, happy to ", "help with that!"]))
    seen = []
    real_urlopen = _urlmod.urlopen
    _urlmod.urlopen = lambda request, timeout=None: resp
    try:
        result = thinker.plan_stream(
            "make a cube", "", [], [], set(catalog), config=_stream_cfg(),
            on_line=lambda line, is_comment: seen.append(line) or True)
    finally:
        _urlmod.urlopen = real_urlopen
    assert result.backend == "mock", (result.backend, result.notes)
    assert seen, "mock fallback never reached the sink"
    assert any("no action lines" in n for n in result.notes), result.notes


def test_plan_stream_loop_done_verdict():
    resp = _StreamResp(_sse_lines(
        ["create.objects.plane size=20\n", "DONE\n"]))
    seen = []
    real_urlopen = _urlmod.urlopen
    _urlmod.urlopen = lambda request, timeout=None: resp
    try:
        result = thinker.plan_stream(
            "task", "", [], [], set(catalog), config=_stream_cfg(),
            loop=True,
            on_line=lambda line, is_comment: seen.append(line) or True)
    finally:
        _urlmod.urlopen = real_urlopen
    assert result.actions_text == "DONE\n", result.actions_text
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert any("verdict DONE" in n for n in result.notes), result.notes


def _dispatch_stubbed(content):
    """Run plan_dispatch against a canned endpoint reply."""
    payload = {"choices": [{"message": {"content": content}}]}

    class _Resp:
        def read(self):
            return json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    real_urlopen = _urlmod.urlopen
    _urlmod.urlopen = lambda request, timeout=None: _Resp()
    try:
        cfg = thinker.ThinkerConfig(
            endpoint="https://x.modal.run/v1/chat/completions",
            api_key="test-key", timeout=10)
        return thinker.plan_dispatch(
            "drive the rover", "", ["- sense: skills/workspace-sense/"],
            [], config=cfg, validate=dispatcher.validate_block)
    finally:
        _urlmod.urlopen = real_urlopen


def test_plan_dispatch_unconfigured_is_empty():
    cfg = thinker.ThinkerConfig(endpoint="", api_key="")
    result = thinker.plan_dispatch("drive the rover", config=cfg,
                                   validate=dispatcher.validate_block)
    assert result.backend == "mock", result.backend
    assert result.actions_text == "", result.actions_text
    assert any("no mock deploy plans" in n for n in result.notes), result.notes


def test_plan_dispatch_valid_plan():
    result = _dispatch_stubbed(
        "```\nDEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n```\n")
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert result.actions_text.splitlines() == [
        "DEPLOY agent=sense", "STEP n=1 agent=sense do=read-stage"], \
        result.actions_text
    assert result.raw, "raw reply not kept"


def test_plan_dispatch_invalid_plan_is_empty():
    result = _dispatch_stubbed("I will deploy the sense agent now\n")
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert result.actions_text == "", result.actions_text
    assert any("dispatch invalid" in n for n in result.notes), result.notes


def test_clean_completion_cuts_glued_channel():
    battery = [
        # vLLM-decoded form (special tokens stripped, header glued).
        (" to=usercreate.objects.plane size=20\nsim.play\n",
         "create.objects.plane size=20\nsim.play\n"),
        # Raw greedy form with full markers + end marker.
        (" to=selfthinking<|eom|> to=user<|message|>sim.play\n<|eot|>extra",
         "sim.play\n"),
        # Lone message marker.
        ("<|message|>sim.play\n", "sim.play\n"),
        # No marker: passthrough.
        ("sim.play\n", "sim.play\n"),
        ("", ""),
    ]
    for raw, want in battery:
        assert thinker.clean_completion(raw) == want, repr(raw)


def test_clean_completion_skips_reasoning_turn():
    raw = (" to=selfWe need to drive...<|eom|>"
           " to=usercreate.objects.plane size=20\n")
    assert thinker.clean_completion(raw) == "create.objects.plane size=20\n"


def test_channel_cleaner_matches_batch():
    battery = [
        " to=usercreate.objects.plane size=20\nsim.play\n",
        "sim.play\n",  # markerless: passthrough incl. tail
        "x" * 5000 + "sim.play\n",  # long markerless: nothing eaten
        "total concentration\n",  # head looks marker-ish, then fails
    ]
    for text in battery:
        want = thinker.clean_completion(text)
        whole = thinker.ChannelCleaner()
        assert whole.feed(text) + whole.flush() == want, repr(text)
        charfed = thinker.ChannelCleaner()
        fed = "".join(charfed.feed(c) for c in text) + charfed.flush()
        assert fed == want, repr(text)


def test_channel_cleaner_reasoning_keeps_lines():
    # Pre-channel reasoning passes through to the extractor (dropped as
    # prose), so kept lines still match batch extraction.
    known = set(catalog)
    text = " to=selfthinks a bit<|eom|> to=usersim.play\n"
    want, _ = thinker.extract_actions(thinker.clean_completion(text), known)
    for pieces in ([text], list(text)):
        ext = thinker.StreamExtractor(known)
        cleaner = thinker.ChannelCleaner()
        fed = []
        for piece in pieces:
            fed += ext.feed(cleaner.feed(piece))
        fed += ext.feed(cleaner.flush()) + ext.flush()[0]
        assert [line for _, line in fed] == want.splitlines(), pieces


def test_extract_actions_keeps_glued_first_line():
    known = set(catalog)
    glued = " to=usercreate.objects.plane size=20\nsim.play\n"
    kept, notes = thinker.extract_actions(thinker.clean_completion(glued), known)
    assert kept.splitlines() == ["create.objects.plane size=20", "sim.play"], kept
    assert notes == [], notes
    # Single-line replies used to vanish entirely.
    kept, _ = thinker.extract_actions(thinker.clean_completion(" to=usersim.play"), known)
    assert kept == "sim.play", kept


def test_plan_stream_strips_glued_channel():
    # Marker split across SSE deltas, like live token streaming.
    resp = _StreamResp(_sse_lines(
        [" to", "=usercreate.objects.plane", " size=20\nsim", ".play\n"]))
    seen = []
    real_urlopen = _urlmod.urlopen
    _urlmod.urlopen = lambda request, timeout=None: resp
    try:
        result = thinker.plan_stream(
            "play the sim", "", ["sim.play"], [], set(catalog),
            config=_stream_cfg(),
            on_line=lambda line, is_comment: seen.append(
                (line, is_comment)) or True)
    finally:
        _urlmod.urlopen = real_urlopen
    assert seen == [("create.objects.plane size=20", False),
                    ("sim.play", False)], seen
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert result.raw.startswith(" to=user"), result.raw  # raw kept verbatim


def test_plan_dispatch_strips_glued_channel():
    result = _dispatch_stubbed(
        " to=userDEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n")
    assert result.backend == "glimmer", (result.backend, result.notes)
    assert result.actions_text.splitlines() == [
        "DEPLOY agent=sense", "STEP n=1 agent=sense do=read-stage"], \
        result.actions_text


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
