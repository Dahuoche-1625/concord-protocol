# Bridge Loop Pilot Acceptance Criteria

Use this checklist to decide whether a concrete project-side pilot instance passes the v0.2 bridge loop test.

The protocol repository contains templates only. A real task instance should live in the adopting project, for example:

```text
blacklight_factory/runtime_mesh/pilot/TASK-0001/
├── bridge_objects/
│   ├── task_contract.json
│   ├── task_dispatch.json
│   ├── task_lease.json
│   ├── execution_receipt.json
│   └── review_result.json
├── audit/
│   └── audit.jsonl
├── artifacts/
└── logs/
```

## Positive Path

- [ ] `TaskContract` has `task_mode: "bridge"`.
- [ ] `TaskContract.assigned_agent` is `null` before lease claim.
- [ ] `TaskContract.input_refs` disclose only minimum project context.
- [ ] `TaskContract.redactions` list excluded secrets or broad project facts.
- [ ] `TaskContract.acceptance_criteria` are concrete and verifiable.
- [ ] `TaskContract.contract_clarity_score >= 3`.
- [ ] `TaskDispatch` references the contract and target mesh.
- [ ] `TaskLease` binds the task to exactly one `agent_id` and `node_id`.
- [ ] `TaskLease.claim_proof` is present.
- [ ] `ExecutionReceipt.artifact_refs` point to real outputs in the project instance.
- [ ] `ExecutionReceipt.execution_hash` is reproducible.
- [ ] `ReviewResult` references the receipt under review.
- [ ] Every transition has an append-only audit event.

## Negative Path

- [ ] Tampered `source_proof` is rejected.
- [ ] Fake `claim_proof` is rejected.
- [ ] Artifact hash mismatch is rejected or marked invalid.
- [ ] `contract_clarity_score < 3` is refused before execution.
- [ ] Protocol version mismatch is rejected before dispatch or claim.
- [ ] Out-of-scope artifact path is invalidated by `guarded_verify`.
- [ ] Expired lease cannot write a valid completion receipt.

## Pass Condition

The pilot passes only when:

```text
positive path succeeds once
negative path rejects expected failures
audit chain is complete
no project facts leak outside declared input_refs
```
