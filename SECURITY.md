# Security Model — Agent Protocol v0.1-alpha

> **IMPORTANT**: V0.1 is `verify_only`, NOT a sandbox. Read this before deploying.

## What V0.1 protects against

| Threat | Protection | Method |
|--------|-----------|--------|
| Agent writes outside its allowed scope | ✅ Detected | `workspace_delta` vs `result_scope` + `artifact_scope` |
| Agent modifies control files (identities, boundaries, manifest) | ✅ Detected | `protected_scope` + `expected_guard_writes` |
| Agent declares capabilities it cannot prove | ✅ Gated | `CapabilityRecord.evidence_refs` required; empty → `probation` |
| Agent submits result for a task it cannot execute | ✅ Gated | `TaskContract.required_capabilities` checked pre-execution |
| Serial dependency chain broken | ✅ Gated | `depends_on` checked pre-execution |
| Agent impersonates another agent | ⚠️ Partial | `file_bus_v1` trusts filesystem ownership; signature/token mode deferred |
| Result silently altered after guard check | ⚠️ Partial | `atomic_write` required; post-check verifies output_refs exist |

## What V0.1 does NOT protect against

| Threat | Why | Planned fix |
|--------|-----|------------|
| **Agent reads forbidden files** (`.env`, credentials) | `read_disclosure_only: true` — guard only checks `source_refs`, cannot intercept OS-level reads | v0.2 enforced sandbox |
| **Agent writes out-of-scope files** | `verify_only` — detects but doesn't prevent the write. Result is invalidated, but the file exists. | v0.2 enforced sandbox |
| **Agent tampers with agent identities** (in `file_bus_v1` mode) | Identity stored in filesystem — no cryptographic verification | v0.2 signature/token identity |
| **Two agents race on the same file** | No distributed lock | Application-level lock file, or v0.2 task-level lock |
| **Guard itself is compromised** | Guard is a script in the same filesystem | v0.2 guard hash verification |

## Security boundaries

```
                    ┌──────────────────────────┐
                    │     Workspace             │
                    │                           │
                    │  ┌──────────────────────┐ │
                    │  │  protected_scope      │ │
                    │  │  (guard + config)     │ │ ← Agent must not write
                    │  │  .framework_guard/    │ │
                    │  │  config/agent_*       │ │
                    │  └──────────────────────┘ │
                    │                           │
                    │  ┌──────────────────────┐ │
                    │  │  Agent scope          │ │
                    │  │  result_scope +       │ │ ← Agent may write
                    │  │  artifact_scope       │ │   (monitored)
                    │  └──────────────────────┘ │
                    │                           │
                    │  ┌──────────────────────┐ │
                    │  │  Unmonitored          │ │
                    │  │  (excluded dirs)      │ │ ← Not scanned
                    │  │  .git/ cache/ media/   │ │
                    │  └──────────────────────┘ │
                    └──────────────────────────┘
```

## Audit trail

Every guard check writes to `audit/` (append-only JSONL). Events include:

- `task_start` — pre-execution manifest
- `task_complete` — post-execution delta (pass)
- `boundary_violation` — blocking violation (write out of scope, control file modified)
- `capability_change` — automatic capability downgrade after 3 violations
- `identity_change` — manual identity status change

Violations are recorded with: `task_id`, `agent_id`, `file_delta`, `violations[]`, `warnings[]`.

## Reporting vulnerabilities

This is an alpha protocol. If you find a security vulnerability in the design or reference implementation, please open an issue with the `security` label. Do NOT report vulnerabilities from your own implementation or deployment.

## Responsible use

Do NOT deploy V0.1 in production environments where:
- Agents handle sensitive data (credentials, PII, financial data)
- Write boundaries are safety-critical
- Agent identity compromise would cause real-world harm

V0.1 is a **detection layer**, not a prevention layer. Use it as a guardrail, not a gate.
