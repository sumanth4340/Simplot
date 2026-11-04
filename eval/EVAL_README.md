# Eval set: scored gates for the Action Reasoner

12 tasks with unseen wordings (nothing in this file appears in the
training builders): 8 action tasks + 4 dispatch tasks. Every task pins
one expected skill; the pins lock current retrieval behavior — re-pin
deliberately after a routing change, never to chase a score.

## What it measures

- **action valid-line rate**: fraction of emitted action lines that pass
  `protocol.validate` (micro-averaged over lines, comments excluded).
- **dispatch accept rate**: fraction of dispatch replies accepted by
  `dispatcher.validate_block` (roster, ordering, xval rules).
- **skill hit rate**: fraction of tasks whose expected skill is in the
  `select_skills` top-5. This scores the router, not the model.

## Run it

```
python action-reasoner/eval/run_eval.py --backend mock
python action-reasoner/eval/run_eval.py --backend endpoint --out report.json
```

`mock` is the offline floor (dispatch unsupported there by design).
`endpoint` needs `GLIMMER_ENDPOINT` + `GLIMMER_API_KEY` and sends the
guided regex when the artifact exists, exactly like the GUI.

## Run-2 bar (guidance, not a gate yet)

Beat mock on valid-line rate with zero prose, dispatch accept 4/4, and
skill hits 12/12. Promote to a release gate once the endpoint clears it
twice in a row.
