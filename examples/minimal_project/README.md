# Minimal Project Example

This directory demonstrates the minimum files needed to adopt the Agent Protocol v0.1 in a file-driven project.

## Overview

Two agents collaborating on a shared task:

- **agent-alpha**: executes code and writes results
- **agent-beta**: reviews outputs

## Setup Steps

1. Create `framework_manifest.json` at project root
2. Register agent identities in `config/agent_identities/`
3. Define agent boundaries in `config/agent_boundaries/`
4. Declare agent capabilities in `config/agent_capabilities/`
5. Create a task in `TASKS/active/`
6. Run `file_bus_guard_v0` before and after agent execution

## Files

```
minimal_project/
├── framework_manifest.json
├── config/
│   ├── agent_identities/
│   │   ├── agent-alpha.json
│   │   └── agent-beta.json
│   ├── agent_boundaries/
│   │   ├── agent-alpha.json
│   │   └── agent-beta.json
│   └── agent_capabilities/
│       ├── agent-alpha.json
│       └── agent-beta.json
├── TASKS/
│   └── active/
│       └── TASK-0001/
│           └── task.json
├── agents/
│   ├── agent-alpha/
│   │   └── results/
│   │       └── TASK-0001/
│   │           └── result.json
│   └── agent-beta/
│       └── results/
├── .framework_guard/                    ← created by guard at runtime
│   └── TASK-0001/
│       ├── allowed_manifest.json
│       ├── workspace_manifest.json
│       └── expected_guard_writes.json
└── audit/                               ← created by guard at runtime
    └── audit_2026-05-28.jsonl
```
