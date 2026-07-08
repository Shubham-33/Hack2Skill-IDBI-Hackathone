# Directives (Layer 1 — SOPs)

Each directive is a Markdown SOP describing **what** to accomplish. The orchestrator
(the agent) reads a directive, decides **how**, and calls the deterministic scripts in
`execution/` to do the work.

## Writing a directive

Use this template. Keep it concrete — write it like instructions for a mid-level employee.

```markdown
# <Directive Name>

## Goal
One or two sentences on the outcome this produces.

## Inputs
- What the caller/user must provide (fields, URLs, IDs, files).

## Tools / Scripts
- `execution/<script>.py` — what it does, how to invoke it, key flags.
- List every execution tool this directive relies on. Create scripts only if none exist.

## Steps
1. ...
2. ...

## Outputs
- Where the deliverable lands (e.g. a Google Sheet URL) and its shape.

## Edge cases & learnings
- Known API limits, retries, timing, gotchas. Update this section as you learn.
```

## Rules
- Directives are living documents — update the **Edge cases & learnings** section whenever
  you discover a constraint or better approach.
- Do **not** create or overwrite directives without asking, unless explicitly told to.
