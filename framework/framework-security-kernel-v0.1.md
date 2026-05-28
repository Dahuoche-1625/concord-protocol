# Framework Security Kernel v0.1

> Status: discussion-draft
> Goal: A minimal executable security kernel. Answers three questions: Who are you? What can you do? How do you prove you stayed within bounds?
> Principle: Shrink, don't expand. Phase 1 builds the police station and courthouse. Phase 2 builds the DMV and zoning board.

---

## 1. V0.1 Scope

V0.1 is NOT a complete framework. It does ONE thing: **make agent behavior verifiable, recordable, and blockable**.

Out of scope for V0.1:
- Dynamic role binding (v0.2)
- Context assembly policies (v0.2)
- Memory management policies (v0.2 — only source_refs minimum rule retained)
- Skill registration management (v0.2)
- Review gates and escalation policies (v0.2)
- Project operational objects (v0.3 — project layer builds these)

---

## 2. Minimum Objects

V0.1 retains only 6 core objects + 2 execution mechanisms:

### 2.1 Core Objects

```
FrameworkManifest     Framework declaration
AgentIdentity         Identity verification
AgentBoundary         Permission boundary
CapabilityRecord      Capability declaration
TaskContract          Task contract
OutputContract        Output contract
```

### 2.2 Execution Mechanisms

```
RuntimeGuard          Runtime verification layer
AuditLog              Audit trail
```

---

## 3. FrameworkManifest

Project-level declaration for adopting the framework layer. Defines version, identity registration method, and default policies.

```json
{
  "framework_version": "0.1",
  "protocol_version": "0.1",
  "project_id": "example_project",
  "identity_mode": "file_bus_v1 | signature | token",
  "identity_required": true,
  "default_deny": true,
  "guard_mode": "verify_only",
  "protected_scope": [
    ".framework_guard/",
    "audit/",
    "config/agent_identities/",
    "config/agent_boundaries/",
    "framework_manifest.json"
  ],
  "guard_workspace_excludes": [".git", "node_modules", "vendor", "archive", "cache"],
  "audit_log": true,
  "runtime_adapter": "file_bus_v1"
}
```

Hard rules:
- `identity_required: true` — results from unregistered agents are invalid.
- `default_deny: true` — any operation not explicitly allowed in AgentBoundary is denied.
- `guard_mode` is fixed to `verify_only` in V0.1 — detects and blocks result acceptance, does not prevent file operations. Upgraded to `enforced` in v0.2.
- `protected_scope` — paths monitored by RuntimeGuard. workspace_manifest includes these (does not exclude them). Agent modifications to protected_scope that don't match `expected_guard_writes` → `control_file_modified` (blocking violation).
- `guard_workspace_excludes` — directories excluded from workspace_manifest scanning. **Directory-level paths only. No file extension wildcards** (e.g., `*.mp4` would weaken boundary detection). Large files still record path/mtime/size, just skip hash.

---

## 4. AgentIdentity

No more bare-string `agent_id`. Identity must be verifiable.

Identity is stored in two layers:

```
config/agent_identities/{agent_id}.json   ← project-level registry, maintained by trusted agent/human (authoritative source)
agents/{name}/identity.json               ← agent local read-only copy or reference
```

Project-level registry format:

```json
{
  "agent_id": "agent-alpha",
  "display_name": "Agent Alpha",
  "identity_proof": {
    "mode": "file_bus_v1 | signature | token",
    "public_key_ref": null
  },
  "registered_at": "ISO8601",
  "registered_by": "human | agent_id",
  "status": "active | disabled"
}
```

Verification rules:
- `file_bus_v1` mode: Registry files are written by trusted agent or human to `config/agent_identities/`. Agents cannot modify this directory. RuntimeGuard reads the registry file for identity verification — does NOT trust the agent's local `identity.json`.
- `signature` mode: Results and task outputs must include signatures. RuntimeGuard verifies using `public_key_ref` from the registry.
- `token` mode: Agent carries a short-lived token. RuntimeGuard validates token expiry and scope.
- `status` uses only `active` / `disabled`. Capability-level degradation is managed by `CapabilityRecord.status`, not mixed into the identity layer.

V0.1 recommendation: start with `file_bus_v1` — simple, auditable, no key management infrastructure needed.

---

## 5. AgentBoundary

Whitelist mode. Any operation NOT in `allowed` is denied.

```json
{
  "agent_id": "agent-alpha",
  "allowed_actions": [
    "read_project_context",
    "write_task_result",
    "propose_changes",
    "send_notification"
  ],
  "denied_actions": [
    "write_credentials",
    "delete_project_state",
    "approve_own_output",
    "modify_agent_identity"
  ],
  "result_scope": [
    "agents/agent-alpha/results/"
  ],
  "artifact_scope": [
    "MEMORY/agent/agent-alpha/",
    "NOTIFICATIONS/"
  ],
  "read_scope": [
    "project_manifest.json",
    "source_of_truth.md",
    "TASKS/active/",
    "TASKS/archive/",
    "MEMORY/project/",
    "MEMORY/framework/",
    "SKILLS/"
  ],
  "read_disclosure_only": true,
  "forbidden_read": [
    ".env",
    "credentials/",
    "config/agent_identities/",
    "agents/*/boundary.json",
    "MEMORY/agent/*"
  ],
  "risk_level": "standard",
  "max_parallel_tasks": 1
}
```

Field descriptions:
- `result_scope` — Where the agent may write `result.json`. Control files like `task.json` are NOT in this scope — agents cannot modify their own task contracts.
- `artifact_scope` — Where the agent may write artifacts. Separated from `result_scope` so RuntimeGuard can validate both write types independently.
- `read_disclosure_only` (fixed to `true` in V0.1) — read_scope verification is "reference/disclosure checking". RuntimeGuard only checks whether source_refs cite forbidden paths, NOT whether the agent actually read them. Actual read interception is v0.2 enforced sandbox.

Hard rules:
1. Default deny — all operations not in `allowed_actions` are rejected by RuntimeGuard.
2. `result_scope` + `artifact_scope` together define all paths the agent may write to. Out-of-scope writes → `invalid` result.
3. `forbidden_read` has highest priority — source_refs citing these paths are flagged even if the path is in `read_scope`.
4. Agent must not modify its own AgentBoundary or AgentIdentity registry files. These modifications require a trusted agent or human.
5. Agent must not approve its own output. `approve_own_output` must be in `denied_actions`.
6. V0.1 read_scope mode is **reference checking** (`read_disclosure_only: true`): RuntimeGuard checks source_refs against `forbidden_read`, but does not intercept actual OS-level reads. Read interception is v0.2.

---

## 6. CapabilityRecord

Capability declaration must include verification evidence.

```json
{
  "agent_id": "agent-alpha",
  "capability": "code_execution",
  "description": "Can read project code, modify files, run tests, and submit structured results",
  "verification": {
    "method": "task_history",
    "evidence_refs": [
      "TASK-0001/result.json",
      "TASK-0003/result.json"
    ],
    "last_verified_at": "ISO8601",
    "verified_by": "human | agent_id"
  },
  "risk_level": "medium",
  "confidence": "high | medium | low",
  "status": "active | probation | restricted"
}
```

Verification rules:
- `evidence_refs` must not be empty. Empty array → `confidence` forced to `low`, `status` to `probation`.
- `task_history` verification: provide at least N successfully completed task results of the same type.
- `manual_review` verification: marked after review by human or trusted agent.
- `status: restricted` — for `risk_level: high` tasks, this capability is treated as unsatisfied.
- 3 consecutive RuntimeGuard boundary violations → CapabilityRecord.status auto-downgraded to restricted (no human approval required).
- CapabilityRecord.status controls task admission. AgentIdentity.status only controls identity validity (active = can accept tasks, disabled = cannot accept any tasks), not capability evaluation.

---

## 7. TaskContract

A contract the agent must satisfy before accepting a task.

```json
{
  "task_id": "TASK-0001",
  "project_id": "example_project",
  "required_capabilities": ["code_execution"],
  "assigned_agent": "agent-alpha",
  "depends_on": [],
  "dependency_result_refs": {
    "TASK-0000": "agents/agent-beta/results/TASK-0000/result.json"
  },
  "input_refs": [],
  "risk_level": "low | medium | high",
  "timeout_sec": 1800,
  "status": "pending | in_progress | partial_done | done | failed | blocked | invalid"
}
```

Field descriptions:
- `depends_on` — serial dependency chain. TASK-raw → TASK-process → TASK-upload expressed through this field.
- `dependency_result_refs` — optional. If `depends_on` is non-empty, the orchestrator should populate upstream result paths when creating the task. If not provided, RuntimeGuard resolves by reading the upstream task.json's `assigned_agent`.
- `partial_done` — task partially completed but blocked (e.g., 5 outputs done, 1 failed). Must include completed output_refs.
- `invalid` — RuntimeGuard detected a boundary violation. This task's result cannot enter `done`.

Rejection conditions:
- AgentIdentity.status is `disabled` → reject all tasks.
- Agent does not satisfy `required_capabilities` → reject (CapabilityRecord.status `restricted` means the capability is treated as unsatisfied for `risk_level: high` tasks).
- Agent's max_parallel_tasks reached → reject.
- `depends_on` not completed → reject.

---

## 8. OutputContract

Minimum requirements for agent outputs.

```json
{
  "task_id": "TASK-0001",
  "result_required": true,
  "summary_required": true,
  "output_refs_required": true,
  "source_refs_required": true,
  "atomic_write_required": true,
  "verification_refs_required": false
}
```

Hard rules:
- stdout is not a formal result.
- Chat messages are not formal results.
- `result.json` is the sole basis for completion confirmation.
- `output_refs` must point to completed formal files, with paths within AgentBoundary.result_scope + artifact_scope.
- `source_refs` must point to referenced input or context files.
- `atomic_write`: result.json must be written to a temp file first, then renamed to the final location. A "half-written" result is not allowed.

---

## 9. RuntimeGuard

V0.1 does not aim for true sandboxing. Start with `verify_only`: **detect, record, block result acceptance**.

### 9.1 Execution Flow

```
file_bus_guard_v0 verification flow:

1.  Read task.json, confirm task_id and assigned_agent
2.  Read authoritative identity from config/agent_identities/{agent_id}.json, verify agent exists and status != disabled
3.  Verify agent's CapabilityRecord includes task's required_capabilities
4.  Verify task's depends_on are all completed
5.  Pre-execution: guard writes expected_guard_writes for this task:
    a. .framework_guard/{task_id}/allowed_manifest.json
    b. .framework_guard/{task_id}/workspace_manifest.json
    c. .framework_guard/{task_id}/expected_guard_writes.json (records guard's own expected writes)
6.  workspace_manifest scan scope = workspace - guard_workspace_excludes (does NOT exclude protected_scope)
7.  [Agent executes task]
8.  Post-execution: read result.json
9.  Verify output_refs are all within result_scope + artifact_scope
10. Compute workspace_delta against workspace_manifest
11. Boundary detection — three-way check:
    a. workspace_delta path not in scope, not in protected_scope → blocking: write_out_of_scope
    b. workspace_delta path in protected_scope, not matching expected_guard_writes → blocking: control_file_modified
    c. workspace_delta path in protected_scope, matching expected_guard_writes → allow (guard's own writes)
12. source_refs reference check: verify no forbidden_read paths (V0.1 = warning only)
13. Write AuditLog
14. If blocking_violations → result invalid, trigger capability downgrade check
15. If only warnings → result done, AuditLog records warnings
16. No violations → result done
```

### 9.2 workspace_manifest & protected_scope

**Core principle**: Do NOT exclude `protected_scope` from workspace scan. Instead, use `expected_guard_writes` to distinguish guard's own writes from agent tampering.

**workspace_manifest** — scans the project workspace's monitorable scope. **Includes** `protected_scope`, only excludes `guard_workspace_excludes`:

```json
{
  "task_id": "TASK-0001",
  "type": "workspace",
  "created_at": "ISO8601",
  "protected_scope": [".framework_guard/", "audit/", "config/agent_identities/", "config/agent_boundaries/", "framework_manifest.json"],
  "excluded_dirs": [".git", "node_modules", "raw_clips", "archive", "cache"],
  "files": [
    {"path": ".framework_guard/TASK-0001/workspace_manifest.json", "mtime": 1716883200, "size": 1024},
    {"path": "audit/audit_2026-05-28.jsonl", "mtime": 1716883100, "size": 5120},
    {"path": "config/agent_identities/agent-alpha.json", "mtime": 1716883000, "size": 256},
    {"path": "MEMORY/project/facts/MEM-0001.json", "mtime": 1716882900, "size": 512}
  ]
}
```

**expected_guard_writes** — guard records all protected_scope paths it will write during this task. Supports exact paths and prefix matching (for date-generated audit files):

```json
{
  "task_id": "TASK-0001",
  "expected_guard_writes": [
    ".framework_guard/TASK-0001/allowed_manifest.json",
    ".framework_guard/TASK-0001/workspace_manifest.json",
    ".framework_guard/TASK-0001/expected_guard_writes.json",
    ".framework_guard/TASK-0001/audit_record.json",
    "audit/audit_2026-05-28.jsonl",
    "audit/audit_index.json"
  ]
}
```

Matching rules:
- Exact path: full path equals → match
- Prefix match: path starts with `"audit/"` or `".framework_guard/{task_id}/"` → match

**protected_scope directory structure**:

```
.framework_guard/                       ← per-task guard state (protected_scope)
├── {task_id}/
│   ├── allowed_manifest.json
│   ├── workspace_manifest.json
│   ├── expected_guard_writes.json
│   └── audit_record.json

audit/                                  ← global aggregated audit logs (protected_scope)
├── audit_2026-05-28.jsonl
└── audit_index.json
```

Both are in `protected_scope`. Both are monitored by workspace_manifest.

**Boundary detection algorithm** (three-way check):

```
workspace_delta = compute_delta(workspace_manifest.files, current_workspace)

for each file in workspace_delta.added + workspace_delta.modified:
    if file.path in protected_scope:
        if not match_expected_guard_writes(file.path):
            blocking_violations.append("control_file_modified")  // agent tampered with protected paths
        else:
            continue  // guard's own write, allow
    else if file.path in (result_scope + artifact_scope):
        continue  // agent wrote within allowed scope
    else:
        blocking_violations.append("write_out_of_scope")  // agent wrote out of bounds
```

Delta comparison rules:
- In baseline, not in current → `deleted` (record only, not a violation)
- Not in baseline, in current → `new`
- In both, mtime or size changed → `modified`
- V0.1 does not record file hash (performance), only mtime + size. Optional hash in v0.2.

### 9.3 Violation Classification: blocking vs warning

V0.1 distinguishes two violation classes:

**blocking_violations** (trigger result invalid):
- `write_out_of_scope` — workspace_delta path not in result_scope + artifact_scope, and not in protected_scope
- `control_file_modified` — workspace_delta path in protected_scope, not matching expected_guard_writes

**warnings** (recorded but not blocking, V0.1 mark only):
- `forbidden_reference` — source_refs points to a forbidden_read path
- workspace_delta file deleted within scope (record but don't penalize)

Only `blocking_violations` cause result invalid. Warnings alone → result done, AuditLog records the warning.

### 9.4 read_scope V0.1 Constraints

V0.1's `read_disclosure_only: true` clarifies: RuntimeGuard does **NOT intercept** agent file reads. It only checks whether source_refs cite forbidden paths. If an agent reads `.env` but doesn't cite it in source_refs, V0.1 cannot detect this. This is v0.2 enforced sandbox territory.

source_refs verification rules:
- Check: do source_refs paths match forbidden_read patterns?
- If match → mark as **warning** (reference disclosure), record in AuditLog, do NOT block result
- V0.1 marks but does not block (evidence is indirect; agent can rebut)

### 9.5 verify_only vs enforced

| Mode | Boundary behavior | When |
|------|------------------|------|
| verify_only (V0.1) | Record + block result acceptance | Post-execution |
| enforced (v0.2) | OS-level prevention | During execution |

V0.1's `verify_only` does not prevent the agent from writing out-of-scope files, but detects it via workspace_delta, and blocking_violation causes result invalid. This deliberate transition period validates process correctness before tightening to a real sandbox.

---

## 10. AuditLog

Structured, append-only, immutable audit trail.

### 10.1 Record Format

```json
{
  "event_id": "AUDIT-0001",
  "timestamp": "ISO8601",
  "project_id": "example_project",
  "task_id": "TASK-0001",
  "agent_id": "agent-alpha",
  "event_type": "task_start | task_complete | boundary_violation | capability_change | identity_change | guard_check",
  "event_data": {
    "guard_result": "pass | violation",
    "blocking_violations": [],
    "warnings": [],
    "file_delta": [],
    "workspace_manifest_ref": ".framework_guard/{task_id}/workspace_manifest.json",
    "expected_guard_writes_ref": ".framework_guard/{task_id}/expected_guard_writes.json"
  },
  "source_refs": ["task.json", "result.json"]
}
```

### 10.2 Write Rules

- Append only. No modification. No deletion.
- Every record includes `timestamp` + `source_refs` for traceability.
- Violation events must include `violations` array with specific offending file paths.
- `capability_change` events must include trigger reason (manual downgrade / consecutive violations auto-downgrade).

### 10.3 Storage Location

```
.framework_guard/                       ← per-task guard state (protected_scope)
├── {task_id}/
│   ├── allowed_manifest.json
│   ├── workspace_manifest.json
│   ├── expected_guard_writes.json
│   └── audit_record.json

audit/                                  ← global aggregated audit logs (protected_scope)
├── audit_2026-05-28.jsonl
└── audit_index.json
```

Both are in `protected_scope`. Both are monitored by workspace_manifest. Daily sharding avoids oversized files. `audit_index.json` indexes violation events for quick lookup.

---

## 11. Default Deny Policy

Any operation not in AgentBoundary `allowed_actions` is denied. This is a hard rule, not overrideable by projects.

Default deny list (all agents):
- Write to any `protected_scope` path (`.framework_guard/`, `audit/`, `config/agent_identities/`, `config/agent_boundaries/`, `framework_manifest.json`)
- Read `.env` or `credentials/` directories (source_refs reference check level)
- Execute network operations (unless explicitly authorized)

---

## 12. file_bus_guard_v0 Reference Implementation

Pseudocode:

```
guard(task_id):
    task = read_json("TASKS/active/{task_id}/task.json")
    agent = task.assigned_agent

    // 1. Identity check
    identity = read_json("config/agent_identities/{agent}.json")
    if identity.status == "disabled": return REJECT("agent disabled")

    // 2. Capability check
    caps = read_json("config/agent_capabilities/{agent}.json")
    for cap in task.required_capabilities:
        cap_record = find(caps, cap)
        if not cap_record: return REJECT("missing capability: {cap}")
        if cap_record.status == "restricted" and task.risk_level == "high":
            return REJECT("capability {cap} restricted for high-risk task")

    // 3. Dependency check
    for dep_id in task.depends_on:
        if task.dependency_result_refs and dep_id in task.dependency_result_refs:
            dep_path = task.dependency_result_refs[dep_id]
        else:
            dep_task = read_json("TASKS/active/{dep_id}/task.json")
            dep_agent = dep_task.assigned_agent
            dep_path = "agents/{dep_agent}/results/{dep_id}/result.json"
        dep_result = read_json(dep_path)
        if dep_result.status != "done": return REJECT("dependency {dep_id} not done")

    // 4. Pre-execution: guard writes expected_guard_writes, generates workspace_manifest
    boundary = read_json("config/agent_boundaries/{agent}.json")
    framework = read_json("framework_manifest.json")
    scope = boundary.result_scope + boundary.artifact_scope
    protected_scope = framework.protected_scope
    excludes = framework.guard_workspace_excludes
    today = today_date()

    // 4a. Guard records expected protected_scope writes
    expected = [
        ".framework_guard/{task_id}/allowed_manifest.json",
        ".framework_guard/{task_id}/workspace_manifest.json",
        ".framework_guard/{task_id}/expected_guard_writes.json",
        ".framework_guard/{task_id}/audit_record.json",
        "audit/audit_{today}.jsonl",
        "audit/audit_index.json"
    ]
    write_json(".framework_guard/{task_id}/expected_guard_writes.json",
               {task_id, expected_guard_writes: expected})

    // 4b. Generate workspace_manifest (includes protected_scope)
    allowed_manifest = create_file_manifest(scope)
    write_json(".framework_guard/{task_id}/allowed_manifest.json", allowed_manifest)

    workspace_manifest = create_file_manifest(project_root, excludes)
    write_json(".framework_guard/{task_id}/workspace_manifest.json", workspace_manifest)

    write_audit(task_id, agent, "task_start", {expected_guard_writes: expected})

    // 5. [Agent executes task]

    // 6. Output verification
    result = read_json("agents/{agent}/results/{task_id}/result.json")

    blocking_violations = []
    warnings = []

    // 6a. output_refs must be in scope
    for ref in result.output_refs:
        if not ref.startswith_any(scope):
            blocking_violations.append({"type": "output_ref_out_of_scope", "path": ref})

    // 6b. workspace_delta three-way check
    baseline_workspace = read_json(".framework_guard/{task_id}/workspace_manifest.json")
    current_workspace = scan_files(project_root, excludes)
    expected_writes = read_json(
        ".framework_guard/{task_id}/expected_guard_writes.json").expected_guard_writes

    workspace_delta = compute_delta(baseline_workspace.files, current_workspace)

    for file in workspace_delta.added + workspace_delta.modified:
        if file.path.startswith_any(protected_scope):
            if not match_expected(file.path, expected_writes):
                blocking_violations.append({"type": "control_file_modified", "path": file.path})
            // else: guard's own write, allow
        else if not file.path.startswith_any(scope):
            blocking_violations.append({"type": "write_out_of_scope", "path": file.path})

    // 6c. source_refs reference check — V0.1 warning only
    for ref in result.source_refs:
        if ref.matches_any(boundary.forbidden_read):
            warnings.append({
                "type": "forbidden_reference",
                "path": ref,
                "note": "Agent cited a forbidden_read path — V0.1 marks only, does not block"
            })

    // 7. Judgment — only blocking_violations cause invalid
    if blocking_violations:
        result.status = "invalid"
        write_audit(task_id, agent, "boundary_violation", {
            blocking_violations, warnings, file_delta: workspace_delta
        })
        recent = count_violations(agent, days=7)
        if recent >= 3:
            update_capability_status(agent, "restricted", "3 consecutive violations")
            write_audit(task_id, agent, "capability_change", {new_status: "restricted"})
        return REJECT("boundary violation")
    else:
        result.status = "done"
        audit_data = {file_delta: workspace_delta, guard_result: "pass"}
        if warnings:
            audit_data["warnings"] = warnings
        write_audit(task_id, agent, "task_complete", audit_data)
        return ACCEPT
```

---

## 13. Deferred to v0.2

| Object | Reason |
|--------|--------|
| RoleBinding | Needs mature capability model first |
| ContextPolicy | Needs memory system built first |
| MemoryPolicy (full) | V0.1 retains only source_refs minimum rule |
| SkillPolicy | Skill registry infrastructure not built |
| ReviewGate | Needs qualified reviewer + ReviewResult |
| ReviewResult | Depends on ReviewGate |
| ApprovalGate | Needs approval chain infrastructure |
| ApprovalReceipt | Depends on ApprovalGate |
| EscalationPolicy | Needs actual running agents at all escalation levels |
| OperationalObject | Project layer builds these first |
