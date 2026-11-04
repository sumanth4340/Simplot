"""File bridge: drive the in-sim executor from an outside program.

Stdlib only on purpose: no omni/isaac imports, so this module can be
unit-tested with a plain python outside Isaac Sim, exactly like protocol.py.

Layout under ~/action-reasoner-bridge/ (see default_bridge_dir)::

    inbox/        driver drops one *.txt batch per command
                  (same one-action-per-line format as the GUI prompt box)
    outbox/       one <stem>.result.json per batch, plus <stem>.png screenshot
    done/         processed inbox files, moved here after the result lands
    status.json   liveness for the driver: bridge on/off, pending count,
                  last command + its ok flag

The in-sim GUI polls process_inbox(); the outside driver (Muse, a script)
writes inbox files and reads outbox results. Result/status writes are
atomic (tmp file + os.replace) so a polling reader never sees halves.
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

BRIDGE_SUBDIR = "action-reasoner-bridge"
INBOX = "inbox"
OUTBOX = "outbox"
DONE = "done"
STATUS = "status.json"
RESULT_SUFFIX = ".result.json"


def default_bridge_dir() -> Path:
    return Path.home() / BRIDGE_SUBDIR


def ensure_layout(base=None) -> dict:
    """Create (if needed) and return the bridge folders."""
    root = Path(base) if base else default_bridge_dir()
    dirs = {
        "base": root,
        "inbox": root / INBOX,
        "outbox": root / OUTBOX,
        "done": root / DONE,
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def list_pending(inbox_dir) -> list:
    """Sorted *.txt batches waiting in the inbox (hidden files ignored)."""
    try:
        names = sorted(
            p.name for p in Path(inbox_dir).iterdir()
            if p.is_file() and p.suffix.lower() == ".txt"
            and not p.name.startswith(".")
        )
    except OSError:
        return []
    return [Path(inbox_dir) / name for name in names]


def read_status(base) -> dict:
    """Last written status, or {} when missing/corrupt."""
    try:
        data = json.loads((Path(base) / STATUS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_status(base, *, bridge="on", pending=0, last_cmd=None, last_ok=None) -> Path:
    """Atomically write the liveness file. Returns its path."""
    target = Path(base) / STATUS
    payload = {
        "ts": datetime.datetime.now().isoformat(),
        "bridge": bridge,
        "pending": pending,
        "last_cmd": last_cmd,
        "last_ok": last_ok,
    }
    _atomic_write_text(target, json.dumps(payload, indent=2))
    return target


def update_result_shot(result_file, png, ok: bool) -> bool:
    """Patch a result JSON with its screenshot outcome. Returns success."""
    try:
        data = json.loads(Path(result_file).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        data["shot"] = str(png) if ok else None
        data["shot_ok"] = bool(ok)
        _atomic_write_text(result_file, json.dumps(data, indent=2))
        return True
    except (OSError, ValueError):
        return False


def process_inbox(base, run_batch, snapshot_fn=None, log_fn=None) -> list:
    """Run every pending inbox batch. Returns one result dict per batch.

    ``run_batch(text)`` runs the GUI-equivalent validate+execute pass and
    returns {"ok", "lines", "results", "log"}. ``snapshot_fn`` returns the
    stage snapshot string ("" when omitted). ``log_fn`` receives GUI log
    lines when given. A batch that fails still moves to done/; an
    unreadable file is left for the next poll.
    """
    base = Path(base)
    dirs = ensure_layout(base)
    prev = read_status(base)
    last_cmd, last_ok = prev.get("last_cmd"), prev.get("last_ok")
    pending = list_pending(dirs["inbox"])
    finished = []
    for path in pending:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            if log_fn is not None:
                log_fn(f"bridge: skip {path.name} (unreadable now, retry next poll: {exc})")
            continue
        try:
            outcome = run_batch(text)
            ok = bool(outcome.get("ok"))
            lines = list(outcome.get("lines") or [])
            results = list(outcome.get("results") or [])
            log = list(outcome.get("log") or [])
        except Exception as exc:  # never let one batch kill the poll loop
            ok, lines = False, []
            results = [{"key": "", "line": 0, "ok": False,
                        "msg": f"bridge: run failed: {exc}"}]
            log = [f"ERROR: bridge: run failed: {exc}"]
        if snapshot_fn is not None:
            try:
                snapshot = snapshot_fn()
            except Exception as exc:
                snapshot = f"snapshot failed: {exc}"
        else:
            snapshot = ""
        result = {
            "cmd": path.name,
            "ts": datetime.datetime.now().isoformat(),
            "ok": ok,
            "lines": lines,
            "results": results,
            "log": log,
            "snapshot": snapshot,
            "shot": None,
        }
        result_file = dirs["outbox"] / (path.stem + RESULT_SUFFIX)
        _atomic_write_text(result_file, json.dumps(result, indent=2))
        try:
            path.replace(_unique_dest(dirs["done"], path.name))
        except OSError as exc:
            if log_fn is not None:
                log_fn(f"bridge: WARN could not archive {path.name}: {exc}")
        result["stem"] = path.stem
        result["result_file"] = str(result_file)
        finished.append(result)
        last_cmd, last_ok = path.name, ok
        if log_fn is not None:
            log_fn(f"bridge: {path.name} -> {'ok' if ok else 'FAIL'} "
                    f"({len(results)} action(s))")
    write_status(base, bridge="on",
                 pending=len(list_pending(dirs["inbox"])),
                 last_cmd=last_cmd, last_ok=last_ok)
    return finished


def _atomic_write_text(path, text: str) -> None:
    target = Path(path)
    tmp = target.parent / (".tmp_" + target.name)
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


def _unique_dest(folder, name: str) -> Path:
    dest = Path(folder) / name
    if not dest.exists():
        return dest
    stem, suffix = Path(name).stem, Path(name).suffix
    i = 2
    while True:
        cand = Path(folder) / f"{stem}_{i}{suffix}"
        if not cand.exists():
            return cand
        i += 1
