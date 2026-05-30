# Bridge Loop Pilot Templates

This directory contains reusable object templates for a v0.2 bridge loop pilot.

It is intentionally not executable and does not contain concrete project task data. The goal is to define object shape before writing a runner.

## Flow

```text
bridge_objects/task_contract.template.json
-> bridge_objects/task_dispatch.template.json
-> bridge_objects/task_lease.template.json
-> bridge_objects/execution_receipt.template.json
-> bridge_objects/review_result.template.json
-> audit/audit.template.jsonl
```

## Template vs Instance

Protocol repository:

```text
examples/bridge_loop_pilot/
  reusable templates and acceptance criteria
```

Project repository:

```text
runtime_mesh/pilot/TASK-0001/
  concrete task instance filled from templates
```

Do not commit project-specific paths, tokens, drama IDs, deployment variables, or real artifacts into this protocol example.

## Notes

- No secrets are included.
- All IDs are placeholders.
- Artifact paths are placeholders.
- `source_proof`, `claim_proof`, and `execution_hash` are placeholder values for v0.2 validation.
- A real pilot should replace placeholder hashes with reproducible values.
- Use [acceptance_criteria.md](acceptance_criteria.md) to judge project-side pilot instances.

## Intended Pilot

Run one local low-risk task with:

```text
UPLOAD=false
one worker
one task
one receipt
one review
```
