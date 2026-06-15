# Security Model — Concord Protocol v0.2.0-alpha

> **IMPORTANT**: Concord is a contract and verification layer, not an OS sandbox. Read this before deploying.

## Release profiles

| Profile | Purpose | Enforcement level |
|---|---|---|
| v0.1 security kernel | Workspace-boundary detection | `verify_only` |
| v0.2 Bridge contracts | Cross-domain authorization, evidence, revocation, and result validation | `guarded_verify` |

Neither profile intercepts every filesystem or network operation. Runtimes must not advertise `enforced` unless an independent sandbox, container, OS account, or equivalent prevention mechanism is active and verified.

## What the protocol protects against

| Threat | Protection | Method |
|--------|-----------|--------|
| Agent writes outside its allowed scope | ✅ Detected | `workspace_delta` vs `result_scope` + `artifact_scope` |
| Agent modifies control files (identities, boundaries, manifest) | ✅ Detected | `protected_scope` + `expected_guard_writes` |
| Agent declares capabilities it cannot prove | ✅ Gated | `CapabilityRecord.evidence_refs` required; empty → `probation` |
| Agent submits result for a task it cannot execute | ✅ Gated | `TaskContract.required_capabilities` checked pre-execution |
| Serial dependency chain broken | ✅ Gated | `depends_on` checked pre-execution |
| Agent impersonates another agent | ⚠️ Partial | `file_bus_v1` trusts filesystem ownership; signature/token mode deferred |
| Result silently altered after guard check | ⚠️ Partial | `atomic_write` required; post-check verifies output_refs exist |
| Upload contract altered after approval | ✅ Gated | ApprovalGrant binds artifact hash, channel, privacy ceiling, and expiration |
| Revoked approval used by a Runtime | ✅ Gated | Fresh revocation-list check required before execution |
| Approval JSON forged without proof | ✅ Gated | HMAC or signature proof validation |
| Retry creates duplicate external action | ✅ Gated | `idempotency_key` and prior-receipt check |

## What the protocol does NOT protect against

| Threat | Why | Planned fix |
|--------|-----|------------|
| **Agent reads forbidden files** (`.env`, credentials) | Contract disclosure rules cannot intercept OS-level reads | Add an independently verified sandbox or restricted OS identity |
| **Agent writes out-of-scope files** | `guarded_verify` can invalidate and clean known changes, but prevention depends on the host | Add filesystem permissions, sandboxing, or containers |
| **Agent tampers with local identities** | File-backed identity is only as strong as local filesystem ownership | Use signed identities and protected key storage |
| **Two nodes race outside the lease store** | The protocol defines lease semantics, not a distributed consensus service | Use atomic storage or a transactional coordinator |
| **Guard or validator is compromised** | A validator in the same trust domain can be replaced | Verify protocol locks and protect the Runtime release |
| **Secrets are exposed before receipt filtering** | Secret stripping protects persisted outputs, not a compromised process | Keep secrets outside contracts and isolate the execution host |

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

This is an alpha protocol. For design-level issues, follow the private reporting instructions in the repository Security tab when available. Do not place tokens, credentials, private task contracts, or production artifacts in a public issue.

## Responsible use

Do not treat Concord as the only control in environments where:
- Agents handle sensitive data (credentials, PII, financial data)
- Write boundaries are safety-critical
- Agent identity compromise would cause real-world harm

Concord provides executable gates for contract acceptance and result validity. It does not replace host hardening, secret management, network policy, or platform-native authorization.
