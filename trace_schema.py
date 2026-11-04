"""Trace record schema: the one shape every SFT jsonl line must have.

Stdlib only. Both builders (build_traces.py, build_drill_traces.py) and
the future live-trace converter validate every record through
validate_record() before writing it, so a malformed line refuses the
whole task instead of poisoning the dataset.

Shape (mirrored declaratively in traces_schema.json for interop):
  {"messages": [system, user, assistant], "meta": {...}}
  meta: task, backend, validated=true, images>=0, actions=[dotted keys],
        skills=[names]; drill records also carry drill + snapshot.
"""
import re

BACKENDS = ("mock", "drill", "glimmer", "live")
_ROLES = ("system", "user", "assistant")
_KEY_RE = re.compile(r"^[A-Za-z]\w*(\.\w+)+$")


def validate_record(record) -> list:
    """Return [] when the record matches the schema, else error strings."""
    errs = []
    if not isinstance(record, dict):
        return ["record is not an object"]
    messages = record.get("messages")
    if not isinstance(messages, list) or len(messages) != 3:
        errs.append("messages must be a 3-message list")
        messages = []
    for want, msg in zip(_ROLES, messages):
        if not isinstance(msg, dict):
            errs.append(f"message {want} is not an object")
            continue
        if msg.get("role") != want:
            errs.append(f"message role {msg.get('role')!r}, want {want!r}")
        content = msg.get("content")
        if not isinstance(content, str) or not content.strip():
            errs.append(f"message {want} has empty content")
    meta = record.get("meta")
    if not isinstance(meta, dict):
        return errs + ["meta is not an object"]
    if not isinstance(meta.get("task"), str) or not meta["task"].strip():
        errs.append("meta.task must be a non-empty string")
    if meta.get("backend") not in BACKENDS:
        errs.append(f"meta.backend {meta.get('backend')!r} not in {BACKENDS}")
    if meta.get("validated") is not True:
        errs.append("meta.validated must be true")
    images = meta.get("images")
    if not isinstance(images, int) or isinstance(images, bool) or images < 0:
        errs.append(f"meta.images must be an int >= 0, got {images!r}")
        images = 0
    image_files = meta.get("image_files", [])
    if images == 0:
        if image_files:
            errs.append("meta.image_files must be empty when images is 0")
    elif (not isinstance(image_files, list) or len(image_files) != images
            or any(not isinstance(p, str) or not p.strip()
                   for p in image_files)):
        errs.append("meta.image_files must list exactly images paths")
    actions = meta.get("actions")
    dispatch = meta.get("dispatch")
    if dispatch is not None:
        if (not isinstance(dispatch, list) or not dispatch
                or any(not isinstance(d, str) or not d.strip()
                       for d in dispatch)):
            errs.append("meta.dispatch must be a non-empty list of lines")
        if actions != []:
            errs.append("dispatch records must carry actions: []")
    elif not isinstance(actions, list) or not actions:
        errs.append("meta.actions must be a non-empty list")
    else:
        for key in actions:
            if not isinstance(key, str) or not _KEY_RE.match(key):
                errs.append(f"meta.actions has bad key {key!r}")
    skills = meta.get("skills")
    if not isinstance(skills, list) or any(not isinstance(s, str) for s in skills):
        errs.append("meta.skills must be a list of strings")
    if meta.get("backend") == "drill":
        if not isinstance(meta.get("drill"), str) or not meta["drill"].strip():
            errs.append("drill record needs meta.drill")
        if not isinstance(meta.get("snapshot"), str) or not meta["snapshot"].strip():
            errs.append("drill record needs meta.snapshot")
    return errs
