# Domain Separation Model v0.1

> Status: discussion-draft
> Goal: Define how shared protocol layers, isolated project/runtime domains, and bridge objects interact in distributed multi-agent collaboration.
> Relationship: Complements the Framework Security Kernel. The security kernel defines what agents must not do; this model defines who may talk to whom, through which objects.

---

## 1. Purpose

The Domain Separation Model prevents project-specific facts and runtime-specific execution state from collapsing into one implicit shared context.

In distributed agent systems, a project may run across multiple machines, and one runtime mesh may serve multiple projects. Therefore, **Project Domain** and **Runtime Mesh Domain** are not parent/child layers. They are independent domains connected only through explicit bridge objects.

Hard rule:

```text
Project Domain MUST NOT directly invoke Agent.
Runtime Mesh Domain MUST NOT directly read, own, or mutate project facts.
All cross-domain interaction MUST go through Bridge Objects.
```

This rule is the core of the model.

---

## 2. Shared Layers

Shared layers are reusable across projects and runtimes.

```text
Protocol Layer
Framework Layer
Application Layer
```

### 2.1 Protocol Layer

Defines general collaboration rules and object semantics.

Responsible for:
- Domain separation rules
- Bridge object semantics
- Task lifecycle
- Audit requirements
- Governance and upgrade process

Not responsible for:
- Project-specific channels, drama lists, customer records, paths, tokens, or business state
- Runtime-specific machines, installed tools, online status, or process state

### 2.2 Framework Layer

Defines executable constraints.

Responsible for:
- Agent identity
- Agent boundaries
- Capability records
- Task and output contracts
- RuntimeGuard verification
- Default deny and audit rules

The Framework Security Kernel remains the authority for boundary checks and result invalidation.

### 2.3 Application Layer

Defines reusable business workflow templates.

Examples:
- AI account operations
- Video production pipeline
- Data analysis workflow
- Content review workflow

Application Layer may define workflow templates, domain object templates, and skill profiles. It MUST NOT contain one project's live facts or one runtime mesh's live node state.

---

## 3. Isolated Domains

```text
Project Domain
Runtime Mesh Domain
```

These domains are peers. Neither owns the other.

### 3.1 Project Domain

Project Domain is the authority for business intent and project facts.

Responsible for:
- `project_id`
- selected `application_id`
- source of truth references
- project policies
- project state
- approval requirements
- business objects
- output acceptance criteria

Not responsible for:
- choosing a concrete worker process
- knowing which agent process is online
- tracking node heartbeat
- managing task leases
- reading runtime-local logs except through bridge references

### 3.2 Runtime Mesh Domain

Runtime Mesh Domain is the authority for execution capacity and runtime state.

Responsible for:
- `mesh_id`
- node registry
- agent identities available in this mesh
- capability records
- task lease management
- heartbeat and liveness
- execution receipts
- runtime audit events

Not responsible for:
- owning project source of truth
- reading unrestricted project memory
- treating project-specific facts as permanent runtime knowledge
- changing project approval or business policies

Runtime-local objects such as `AgentNode`, `Heartbeat`, and runtime-local process logs are not bridge objects. They remain inside Runtime Mesh Domain unless referenced by an `ExecutionReceipt` or audit event.

### 3.3 Many-to-Many Relationship

A project may dispatch tasks to multiple runtime meshes. A runtime mesh may serve multiple projects.

```text
Project A -- TaskContract -- Runtime Mesh 1
Project A -- TaskContract -- Runtime Mesh 2
Project B -- TaskContract -- Runtime Mesh 1
Project C -- TaskContract -- Runtime Mesh 3
```

The binding exists only for the lifecycle of a task. When the task closes, the binding ends.

---

## 4. Bridge Layer

Bridge Layer is an independent protocol surface. It is not part of Project Domain and not part of Runtime Mesh Domain.

Bridge objects are the only valid cross-domain interface:

```text
TaskContract
TaskDispatch
TaskLease
ExecutionReceipt
ReviewResult
```

### 4.1 Bridge Object Summary

| Object | Purpose | Direction |
| --- | --- | --- |
| `TaskContract` | Defines project intent, required capability, allowed context, gates, and expected outputs | Project-authorized issuer -> Bridge |
| `TaskDispatch` | Publishes a task to an eligible runtime mesh or worker pool | Coordinator/adapter -> Runtime Mesh |
| `TaskLease` | Records exclusive task claim by one worker for a bounded time | Runtime Mesh -> Bridge |
| `ExecutionReceipt` | Reports execution status, artifacts, logs, warnings, and errors | Worker -> Bridge -> Project |
| `ReviewResult` | Records acceptance, rejection, retry, or escalation decision | Reviewer -> Bridge -> Project/Runtime |

---

## 5. Bridge Object Authority

Bridge objects MUST have explicit authority rules.

### 5.1 Coordinator Role

Coordinator Agent is a runtime role, not a new domain.

Rules:
- Coordinator belongs to Runtime Mesh Domain.
- Coordinator MAY create or publish `TaskDispatch` only when authorized by Project Domain.
- Coordinator MUST NOT directly mutate project facts.
- Coordinator MUST NOT bypass Bridge Objects.
- Coordinator summarizes receipts and proposes next actions; it does not become an absolute decision maker.

### 5.2 Object Issuers

| Object | Authorized issuer |
| --- | --- |
| `TaskContract` | Project-authorized human, project agent, or policy adapter |
| `TaskDispatch` | Coordinator or dispatch adapter with project authority |
| `TaskLease` | Runtime mesh lease manager or worker through atomic claim |
| `ExecutionReceipt` | Worker agent that owns the active lease |
| `ReviewResult` | Project-authorized reviewer, owner, review agent, or approval adapter |

### 5.3 Invalid Issuance

A bridge object is invalid when:
- issuer identity cannot be verified
- issuer lacks authority for the object type
- required source references are missing
- object attempts to bypass another required bridge object
- object contains raw secrets or unrestricted project context

### 5.4 Assignment Timing

In single-worker or local `file_bus_v1` mode, a `TaskContract` may include a concrete `assigned_agent` before execution.

In distributed bridge mode, Project Domain SHOULD NOT choose a concrete worker. It SHOULD publish:

```text
required_capabilities
target_mesh
dispatch_policy
```

The concrete worker binding happens only when `TaskLease` is atomically claimed.

Compatibility rule:

```text
Project intent phase: TaskContract describes required capability and output contract.
Runtime claim phase: TaskLease binds task_id to agent_id and node_id.
Guard execution phase: RuntimeGuard may materialize an execution-bound task snapshot containing assigned_agent.
```

This keeps existing `file_bus_v1` guard behavior compatible without making Project Domain depend on runtime worker identity.

---

## 6. Task Lifecycle

The bridge layer owns task lifecycle states.

### 6.1 Minimum States

```text
draft
dispatched
claimed
running
partial_done
done
failed
expired
cancelled
invalid
reviewed
```

### 6.2 State Meaning

| State | Meaning |
| --- | --- |
| `draft` | TaskContract exists but is not published |
| `dispatched` | TaskDispatch exists and task is available for claim |
| `claimed` | Worker holds an active TaskLease |
| `running` | Worker has started execution |
| `partial_done` | Some outputs are complete, but task needs retry, continuation, or review |
| `done` | Worker reports completion and required outputs exist |
| `failed` | Worker reports failure without boundary violation |
| `expired` | Active lease expired before valid receipt |
| `cancelled` | Project-authorized actor cancelled the task |
| `invalid` | RuntimeGuard or bridge validation rejected the result |
| `reviewed` | Project-side review has accepted, rejected, or escalated the result |

### 6.3 Valid Transitions

```text
draft -> dispatched
dispatched -> claimed
dispatched -> cancelled
claimed -> running
claimed -> expired
claimed -> cancelled
running -> partial_done
running -> done
running -> failed
running -> expired
running -> invalid
running -> cancelled
partial_done -> dispatched
partial_done -> reviewed
done -> reviewed
failed -> dispatched
failed -> reviewed
expired -> dispatched
cancelled -> reviewed
invalid -> reviewed
```

Invalid transitions MUST be rejected and audited.

---

## 7. Lease and Retry Rules

Distributed workers require explicit lease semantics.

### 7.1 Lease Rules

- At most one active `TaskLease` may exist for the same `task_id` and `output_contract`.
- Lease claim MUST be atomic.
- Lease MUST include `lease_until`.
- Worker MUST renew lease before expiration for long-running work.
- Expired lease does not prove task failure; it only removes exclusive ownership.
- A worker without an active lease MUST NOT write `ExecutionReceipt` for that task.

### 7.2 Retry Rules

- Retry MUST either reuse the same `task_id` after lease expiration or create a new task with `retry_of`.
- Retry MUST preserve source references to the prior attempt.
- Retry MUST NOT silently overwrite prior receipts.
- New artifacts MUST use unique output references unless the OutputContract explicitly allows replacement.

### 7.3 Idempotency Rules

`ExecutionReceipt` MUST be idempotent.

Minimum idempotency key:

```text
task_id + lease_id + agent_id + attempt
```

Duplicate receipts with the same idempotency key MUST be treated as the same receipt, not as a new completion.

---

## 8. Transport Adapter Contract

The domain model does not require a specific transport. Transport is an adapter.

Supported adapter families may include:

```text
file_bus_v1
git_bus_v1
feishu_bus_v1
http_bus_v1
queue_bus_v1
```

### 8.1 Minimum Adapter Operations

Every transport adapter MUST provide:

```text
create_task_contract
publish_dispatch
list_pending_dispatches
claim_lease_atomically
renew_lease
release_or_close_lease
write_execution_receipt
write_review_result
append_audit_event
read_task_state
```

### 8.2 Required Guarantees

Transport adapter MUST guarantee:
- atomic lease claim
- durable receipt write
- append-only audit events
- stable object IDs
- no silent overwrite of bridge objects
- readable task state for authorized actors

If a transport cannot guarantee atomic lease claim, it MUST be marked `single_worker_only` or `experimental`.

---

## 9. Minimum Project Context Disclosure

TaskContract is the only place where Project Domain discloses context to Runtime Mesh.

Rules:
- Include only the minimum context needed for this task.
- Do not include raw secrets.
- Do not include full project memory dumps.
- Do not include unrestricted source-of-truth access.
- Include explicit `input_refs` instead of vague project instructions.
- Include `context_expires_at` when context should not be reused.
- Include `context_scope` so workers know whether context is task-only, project-limited, or reusable.

Example:

```json
{
  "task_id": "TASK-20260529-001",
  "project_id": "blacklight_factory",
  "application_id": "ai_account_ops",
  "context_scope": "task_only",
  "context_expires_at": "2026-05-30T00:00:00+08:00",
  "input_refs": [
    "feishu://base/drama_main/N626",
    "project://deployment_manifest.local.json"
  ],
  "redactions": [
    "oauth_token",
    "client_secret",
    "full_channel_registry"
  ]
}
```

Runtime Mesh MUST NOT promote task-only context into permanent runtime memory.

---

## 10. Artifact References

ExecutionReceipt MUST prove output existence with verifiable artifact references.

Minimum artifact reference:

```json
{
  "artifact_id": "ART-0001",
  "type": "video | image | audio | text | json | log | other",
  "uri": "outputs/N626-final.mp4",
  "sha256": "optional-if-large-file-policy-skips-hash",
  "size_bytes": 123456,
  "created_at": "2026-05-29T10:00:00Z",
  "media_duration_sec": 3600,
  "producer_agent_id": "workbuddy-win-01",
  "task_id": "TASK-20260529-001"
}
```

Rules:
- `artifact_refs` MUST be present when output is required.
- Large file policies MAY skip hash, but MUST include path/URI, size, and mtime or created timestamp.
- Receipt MUST distinguish final artifacts from logs and intermediates.
- Artifact references MUST stay inside the output contract scope.

---

## 11. Cross-Domain Audit

Every bridge object transition MUST emit an audit event.

Minimum audit fields:

```json
{
  "event_id": "AUDIT-0001",
  "object_type": "TaskLease",
  "object_id": "LEASE-0001",
  "task_id": "TASK-20260529-001",
  "old_status": "dispatched",
  "new_status": "claimed",
  "actor_id": "workbuddy-win-01",
  "actor_domain": "runtime_mesh",
  "timestamp": "2026-05-29T10:00:00Z",
  "source_refs": [
    "tasks/TASK-20260529-001/task_contract.json"
  ]
}
```

Rules:
- Audit log MUST be append-only.
- Cross-domain audit MUST identify actor domain.
- Audit event MUST reference the bridge object that changed.
- ReviewResult MUST reference the ExecutionReceipt under review.
- Invalid transitions MUST be audited even when rejected.

---

## 12. Relationship with Framework Security Kernel

The Domain Separation Model and Framework Security Kernel are complementary.

| Concern | Authority |
| --- | --- |
| Agent identity | Framework Security Kernel |
| Agent write boundary | Framework Security Kernel |
| Capability verification | Framework Security Kernel |
| RuntimeGuard result invalidation | Framework Security Kernel |
| Project/Runtime isolation | Domain Separation Model |
| Bridge object semantics | Domain Separation Model |
| Task lifecycle across domains | Domain Separation Model |
| Lease, retry, transport adapter contract | Domain Separation Model |

Security Kernel question:

```text
Did this agent stay within its allowed boundary?
```

Domain Separation question:

```text
Was this cross-domain interaction authorized, minimal, auditable, and contract-based?
```

Both checks must pass before a result can be accepted.

---

## 13. Minimal Bridge Object Shapes

These shapes are normative field guidance for v0.1. Dedicated JSON Schema files may be added after one reference implementation validates the flow.

### 13.1 TaskDispatch

```json
{
  "dispatch_id": "DISPATCH-0001",
  "task_id": "TASK-0001",
  "project_id": "example_project",
  "target_mesh": "mesh-any | mesh-id",
  "required_capabilities": ["video_pipeline_execution"],
  "dispatch_status": "open | claimed | cancelled | expired",
  "created_at": "ISO8601",
  "created_by": "coordinator-agent-id",
  "source_refs": ["tasks/TASK-0001/task_contract.json"]
}
```

### 13.2 TaskLease

```json
{
  "lease_id": "LEASE-0001",
  "task_id": "TASK-0001",
  "dispatch_id": "DISPATCH-0001",
  "claimed_by": "worker-agent-id",
  "node_id": "node-win-01",
  "claimed_at": "ISO8601",
  "lease_until": "ISO8601",
  "status": "active | renewed | released | expired"
}
```

### 13.3 ExecutionReceipt

```json
{
  "receipt_id": "RECEIPT-0001",
  "task_id": "TASK-0001",
  "lease_id": "LEASE-0001",
  "agent_id": "worker-agent-id",
  "node_id": "node-win-01",
  "status": "partial_done | done | failed | invalid",
  "artifact_refs": [],
  "log_refs": [],
  "warnings": [],
  "errors": [],
  "generated_at": "ISO8601",
  "source_refs": ["runtime/logs/TASK-0001.log"]
}
```

### 13.4 ReviewResult

```json
{
  "review_id": "REVIEW-0001",
  "task_id": "TASK-0001",
  "receipt_id": "RECEIPT-0001",
  "reviewer_id": "owner-or-review-agent",
  "decision": "accepted | rejected | retry_requested | escalated",
  "rationale": "Short reason",
  "next_task_refs": [],
  "reviewed_at": "ISO8601",
  "source_refs": ["receipts/RECEIPT-0001.json"]
}
```

---

## 14. Non-Goals for v0.1

V0.1 does not define:
- a network protocol
- a mandatory queue implementation
- a sandbox
- secret distribution
- global agent reputation
- cross-project memory sharing
- automatic business approval

These may be added later, but they must not weaken the domain separation rule.

---

## 15. Implementation Guidance

Recommended first implementation order:

1. Represent Bridge Objects as files.
2. Use one transport adapter (`file_bus_v1` or project-specific table adapter).
3. Implement atomic `claim_lease`.
4. Require `ExecutionReceipt.artifact_refs`.
5. Append audit events for every status transition.
6. Run Framework Security Kernel checks before accepting `done`.
7. Run Project review before marking `reviewed`.

Do not migrate existing project directories before the bridge flow is proven with one small task.
