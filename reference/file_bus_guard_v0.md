# file_bus_guard_v0 — Reference Implementation Guide

This document explains how to implement the RuntimeGuard verification flow for the `file_bus_v1` adapter.

## Overview

`file_bus_guard_v0` is a post-execution verification script. It does NOT sandbox the agent — it detects boundary violations after the task runs and invalidates the result if violations are found.

## Prerequisites

Before running guard, ensure:

1. `config/agent_identities/{agent_id}.json` — identity registry (trusted agent/human maintained)
2. `config/agent_boundaries/{agent_id}.json` — boundary definition for each agent
3. `config/agent_capabilities/{agent_id}.json` — capability records
4. `framework_manifest.json` — project-level framework configuration

## Lifecycle

```
Pre-execution:                   Post-execution:
                                 
Guard writes:                    Guard checks:
├── expected_guard_writes.json   ├── output_refs → in scope?
├── allowed_manifest.json        ├── workspace_delta → out of scope?
├── workspace_manifest.json      ├── protected_scope → tampered?
└── [Agent runs]                 └── source_refs → forbidden?
```

## Pre-execution Steps

### 1. Generate workspace_manifest

Scan the project workspace, excluding `guard_workspace_excludes` directories. **Include** `protected_scope` paths — do NOT exclude them.

For each file, record: `path`, `mtime`, `size`.

### 2. Generate allowed_manifest

Scan `result_scope` + `artifact_scope` directories. Same format.

### 3. Write expected_guard_writes

List all files the guard itself will write during this task:

```
.framework_guard/{task_id}/allowed_manifest.json
.framework_guard/{task_id}/workspace_manifest.json
.framework_guard/{task_id}/expected_guard_writes.json
.framework_guard/{task_id}/audit_record.json
audit/audit_{today}.jsonl
audit/audit_index.json
```

### 4. Write AuditLog (task_start)

Record identity check, capability check, dependency check results.

## Post-execution Steps

### 1. Read result.json

From path: `agents/{agent_id}/results/{task_id}/result.json` (file_bus_v1 convention).

### 2. Check output_refs

Every path in `result.output_refs` must start with a path in `result_scope` or `artifact_scope`.

### 3. Compute workspace_delta

Compare current workspace (same scan as pre-execution) against `workspace_manifest.json` baseline.

For each `added` or `modified` file:

- If path is in `protected_scope` AND NOT in `expected_guard_writes` → `control_file_modified` (blocking)
- If path is in `protected_scope` AND in `expected_guard_writes` → guard's own write, allow
- If path is in `result_scope + artifact_scope` → agent wrote in scope, allow
- Otherwise → `write_out_of_scope` (blocking)

### 4. Check source_refs

For each path in `result.source_refs`:
- If it matches a `forbidden_read` pattern → `forbidden_reference` (warning, not blocking)

### 5. Judgment

- Any blocking violations → `result.status = "invalid"`, write `boundary_violation` audit record
- Only warnings → `result.status = "done"`, write `task_complete` audit record with warnings
- No violations → `result.status = "done"`, write `task_complete` audit record

### 6. Capability downgrade

Count violations for this agent in the last 7 days. If ≥ 3 → auto-downgrade all CapabilityRecords to `restricted`.

## Implementation Notes

### File Manifest Format

```json
{
  "task_id": "TASK-0001",
  "type": "workspace",
  "created_at": "2026-05-28T10:30:00Z",
  "scope": ["protected_scope", "agent scopes"],
  "excluded_dirs": [".git", "node_modules", "cache"],
  "files": [
    {"path": "MEMORY/project/facts/MEM-0001.json", "mtime": 1716883200, "size": 1024}
  ]
}
```

### Delta Computation

```
baseline_keys = {(file.path, file.mtime, file.size) for file in manifest.files}
current_keys = {(file.path, file.mtime, file.size) for file in current_scan}

added = current_keys - baseline_keys
deleted = baseline_keys - current_keys
modified = {(path, mtime, size) in both but mtime or size changed}
```

V0.1 uses only `mtime` + `size` for performance. No file hash.

### Atomic Write

Result files must be written atomically:

```
write to result.tmp → rename to result.json
```

No "half-written" result files allowed. Guard checks that output_refs files exist and are complete.

### Audit Log Append

Audit records are JSONL (one JSON object per line), append-only:

```jsonl
{"event_id":"AUDIT-0001","timestamp":"2026-05-28T10:30:00Z","project_id":"example_project","task_id":"TASK-0001","agent_id":"agent-alpha","event_type":"task_start",...}
{"event_id":"AUDIT-0002","timestamp":"2026-05-28T10:35:00Z","project_id":"example_project","task_id":"TASK-0001","agent_id":"agent-alpha","event_type":"task_complete",...}
```

Never modify or delete existing lines.

## Minimal Implementation

A minimal guard implementation can be ~200 lines of Python or shell. The full pseudocode is in the [Framework Security Kernel](../framework/framework-security-kernel-v0.1.md#12-file_bus_guard_v0-reference-implementation).

Start with:

1. Read task.json → extract agent_id
2. Read identity, boundary, capabilities from config/
3. Pre-check: identity, capabilities, dependencies
4. Generate manifests
5. Wait for agent result
6. Post-check: output_refs, workspace_delta, source_refs
7. Write audit record
8. Update result status
