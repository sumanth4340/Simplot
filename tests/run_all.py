"""Offline suite runner. Usage: python action-reasoner/tests/run_all.py

Runs every tests/test_*.py in this directory with the current python,
parses each "<n> tests passed" (or "<n>/<n> watcher tests passed")
summary, and exits nonzero when any file fails. Test files stay
directly runnable on their own; this only aggregates them.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_COUNT_RE = re.compile(r"(\d+)(?:/\d+)?(?: watcher)? tests passed")


def main() -> int:
    total, failed = 0, []
    files = sorted(HERE.glob("test_*.py"))
    for path in files:
        proc = subprocess.run([sys.executable, str(path)],
                              capture_output=True, text=True)
        last = (proc.stdout.strip().splitlines() or [""])[
            -1] if proc.stdout else ""
        match = _COUNT_RE.search(last)
        if proc.returncode == 0 and match:
            total += int(match.group(1))
            print(f"{path.name}: {last}")
        else:
            failed.append(path.name)
            print(f"{path.name}: FAILED")
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-5:]
            for line in tail:
                print(f"    {line}")
    print(f"TOTAL: {total} passed, {len(failed)} files failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
