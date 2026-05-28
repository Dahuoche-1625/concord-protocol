# Framework Layer Protocol v0.1 (Extended Draft)

> Status: extended-draft (deferred to v0.2)
> This document is retained as the full 11-object design reference. V0.1 execution target is the [Framework Security Kernel](framework-security-kernel-v0.1.md) (6 objects + 2 mechanisms).

The extended draft defines the complete framework layer vision:

```
Protocol Layer    → General collaboration methods
Framework Layer   → Agent boundaries, capabilities, permissions, context, memory, skills, task contracts, review gates
Project Layer     → Project facts, goals, business state machines, specific tasks
Agent Layer       → Individual agent context, skills, memory, and tool entrypoints
```

## Deferred Objects

These were defined in the original draft but deferred from V0.1:

| Object | Purpose | Target |
|--------|---------|--------|
| RoleBinding | Dynamic agent-to-role binding | v0.2 |
| ContextPolicy | Per-task context assembly rules | v0.2 |
| MemoryPolicy | Full memory lifecycle (scopes, states, promotion) | v0.2 |
| SkillPolicy | Skill registration, risk, and input/output policies | v0.2 |
| ReviewGate | Risk-based review requirements | v0.2 |
| ReviewResult | Structured review outcome | v0.2 |
| ApprovalGate | Approval chain infrastructure | v0.2 |
| ApprovalReceipt | Approval chain records | v0.2 |
| EscalationPolicy | Multi-level exception escalation | v0.2 |

## Memory Model (Preview)

Memory is a cross-layer capability managed by the framework, not a separate fifth layer.

### Scopes

```
protocol memory  — Protocol evolution, general methods, committee decisions
framework memory — Agent boundaries, capability verification, failure patterns
project memory   — Project facts, business decisions, architectural constraints
agent memory     — Per-agent context, preferences, skill usage experience
task memory      — Per-task local process, failure reasons, temporary context
```

### States

```
candidate   — Can hint, cannot be decision basis
reviewed    — Reviewed, can assist decisions
canonical   — Formal memory for its layer
deprecated  — Superseded, retained for traceability
expired     — Expired, excluded from context assembly
```

### Promotion Flow

```
task memory → agent memory → project memory → framework memory → protocol memory
```

Promotion conditions: has source, has reuse value, reviewed by at least one reviewer, contains no project secrets, does not conflict with higher canonical memory.

> Full MemoryPolicy specification is deferred to v0.2. V0.1 only enforces the minimum rule: all memory records must have `source_refs`.
