# Bridge Loop Pilot Example

This example contains the minimum object files for a v0.2 bridge loop pilot.

It is intentionally not executable yet. The goal is to make the protocol objects concrete before writing a runner.

## Flow

```text
bridge_objects/task_contract.json
-> bridge_objects/task_dispatch.json
-> bridge_objects/task_lease.json
-> bridge_objects/execution_receipt.json
-> bridge_objects/review_result.json
-> audit/audit.jsonl
```

## Notes

- No secrets are included.
- All IDs are examples.
- Artifact paths point to placeholder files.
- `source_proof`, `claim_proof`, and `execution_hash` are placeholder values for v0.2 validation.
- A real pilot should replace placeholder hashes with reproducible values.

## Intended Pilot

Run one local low-risk task with:

```text
UPLOAD=false
one worker
one task
one receipt
one review
```

