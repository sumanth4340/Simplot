"""Build the guided-decoding regex for Glimmer action output (vLLM guided_regex).

The pattern constrains SHAPE only (no prose can be emitted); exact key
vocabulary stays enforced post-generation by protocol.validate, and
dispatch semantics by dispatcher.validate_block. That split keeps the
regex small and stable across catalog edits.

Covers one full completion: action lines, dispatch lines, DONE, # comments.

Usage:
  python action-reasoner/build_guided_regex.py
Writes: ext/.../executor/data/guided_action_regex.txt
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXT_DATA = (ROOT / "ext" / "isaacsim.action.reasoner.executor" / "data")
OUT = EXT_DATA / "guided_action_regex.txt"

COMMENT = r"#[^\n]*"
VERDICT = r"DONE"
DISPATCH = r"(DEPLOY|STEP|PARALLEL|COWORK)(\s+[A-Za-z_]+=[^\s]+)+"
ACTION = r"[A-Za-z]\w*(\.\w+)+(\s+\w+=[^\s]+)*"
LINE = f"({COMMENT}|{VERDICT}|{DISPATCH}|{ACTION})"
FULL = f"({LINE}\\n?)+"


def main() -> int:
    OUT.write_text(FULL + "\n", encoding="utf-8")
    print(f"guided regex ({len(FULL)} chars) -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
