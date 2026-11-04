"""Observer: viewport screenshots so actions can be verified visually.

All Isaac/Kit imports are guarded so this module still imports outside
Isaac Sim (the GUI and tests can probe availability anywhere).

Backend is the sanctioned Isaac Sim 6 capture path
(:func:`isaacsim.test.utils.image_capture.capture_viewport_screenshot_async`),
which renders the active viewport through a replicator rgb annotator:
no UI chrome, works headless. It is async, so :func:`capture_viewport`
schedules the capture on Kit's asyncio loop and reports completion
through an ``on_done(ok, message)`` callback.
"""
from __future__ import annotations

import datetime
from pathlib import Path

try:
    import isaacsim.core.experimental.utils.app as _app_utils

    _APP_OK = True
except Exception:  # pragma: no cover - outside Isaac Sim
    _APP_OK = False

CAPTURE_SUBDIR = "action-reasoner-captures"
CAPTURE_EXT = "isaacsim.test.utils"


def default_capture_dir() -> Path:
    return Path.home() / CAPTURE_SUBDIR


def next_capture_path(prefix: str = "snapshot", directory=None) -> Path:
    """Timestamped PNG path for the next capture (parent not created)."""
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    base = directory or default_capture_dir()
    candidate = Path(base) / f"{prefix}_{stamp}.png"
    i = 1
    while candidate.exists():
        i += 1
        candidate = Path(base) / f"{prefix}_{stamp}_{i}.png"
    return candidate


def backend_available() -> tuple:
    """(ok, reason) for the capture backend."""
    if not _APP_OK:
        return False, "not running inside Isaac Sim"
    return True, "viewport rgb via isaacsim.test.utils"


def _is_playing() -> bool:
    try:
        import omni.timeline

        return bool(omni.timeline.get_timeline_interface().is_playing())
    except Exception:
        return False


async def _capture_live_async(path: str) -> int:
    """Capture while the timeline plays, without the replicator orchestrator.

    The stock ``capture_viewport_screenshot_async`` steps the orchestrator,
    which stops a playing timeline (seen live: "resetting the animation
    timeline" right after every capture). While playing, frames render
    continuously, so attaching the rgb annotator and waiting out two app
    updates yields a fresh frame with no timeline interference. Mirrors
    ``capture_annotator_data_async`` (attach/read/detach), minus its
    orchestrator step.
    """
    import omni.kit.app
    import omni.kit.viewport.utility as viewport_utils
    import omni.replicator.core as rep
    from isaacsim.test.utils.image_io import save_rgb_image

    viewport_api = viewport_utils.get_active_viewport()
    render_product = getattr(viewport_api, "render_product_path", None)
    if not render_product:
        raise RuntimeError("no active viewport render product")
    annot = rep.AnnotatorRegistry.get_annotator("rgb")
    annot.attach(render_product)
    try:
        app = omni.kit.app.get_app()
        await app.next_update_async()
        await app.next_update_async()
        data = annot.get_data()
    finally:
        try:
            annot.detach()
        except Exception:
            pass
    if data is None:
        raise RuntimeError("annotator returned no data")
    target = Path(path)
    save_rgb_image(data, str(target.parent), target.name)
    if not target.is_file():
        raise RuntimeError(f"capture backend failed for {path}")
    return target.stat().st_size


async def _capture_async(path: str) -> int:
    """Enable the capture ext if needed, capture, return file size."""
    if not _app_utils.is_extension_enabled(CAPTURE_EXT):
        if not _app_utils.enable_extension(CAPTURE_EXT):
            raise RuntimeError(f"could not enable extension {CAPTURE_EXT}")
        await _app_utils.update_app_async(steps=5)
    if _is_playing():
        return await _capture_live_async(str(path))
    from isaacsim.test.utils.image_capture import (
        capture_viewport_screenshot_async,
    )

    ok = await capture_viewport_screenshot_async(path)
    if not ok:
        raise RuntimeError(f"capture backend failed for {path}")
    return Path(path).stat().st_size


def capture_viewport(path=None, on_done=None) -> tuple:
    """Start an async viewport capture -> (started, message).

    ``path`` defaults to a timestamped PNG under ~/action-reasoner-captures.
    ``on_done``, when given, is called as ``on_done(ok, message)`` on
    completion. Never raises for capture failures; they arrive via
    ``on_done(False, ...)`` (or the returned message when not started).
    """
    available, reason = backend_available()
    if not available:
        return False, f"no capture backend ({reason})"
    target = Path(path) if path else next_capture_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return False, f"cannot create capture dir: {exc}"
    try:
        import asyncio

        future = asyncio.ensure_future(_capture_async(str(target)))
    except RuntimeError as exc:
        return False, f"no event loop to run capture: {exc}"

    def _done(fut):
        try:
            size = fut.result()
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller
            if on_done is not None:
                on_done(False, f"screenshot failed: {exc}")
        else:
            if on_done is not None:
                on_done(True, f"screenshot saved: {target} ({size} bytes)")

    try:
        future.add_done_callback(_done)
    except Exception as exc:
        return False, f"cannot track capture: {exc}"
    return True, f"capturing viewport -> {target}"


def describe() -> str:
    ok, reason = backend_available()
    return f"observer: {'ready (' + reason + ')' if ok else 'unavailable (' + reason + ')'}"
