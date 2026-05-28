# Reusable Multi-Agent Protocol v0.1 (Draft)

> Status: discussion-draft
> Goal: Abstract a reusable agent collaboration protocol that is independent of specific projects, roles, models, applications, or skills.

---

## 1. Protocol Positioning

This protocol is not a project runbook, nor is it a scheduling script for any specific agent.

It defines a set of general methods so that multiple agents across different projects can:

- Read project facts
- Form architectural consensus
- Generate tasks and constraints
- Execute, verify, and retrospect
- Feed reusable experience back as protocol upgrades

The protocol layer answers **how to collaborate, decide, verify, and upgrade**. The project layer answers **what to do, where, by whom, with what tools**.

---

## 2. Layer Model

### 2.1 Protocol Layer

Defines general collaboration methods, not bound to project business.

Responsible for:
- Agent identity, capability, boundary declaration
- Task, result, review, verification, and decision objects
- Multi-agent committee consensus flow
- Protocol upgrade process
- Project onboarding requirements
- Failure, timeout, rollback, audit, and archival rules

Not responsible for:
- Writing project-specific code or content
- Assuming a permanent role for any agent
- Requiring any specific model, application, CLI, MCP, or skill

### 2.2 Framework Layer

Translates protocol abstractions into executable constraints.

Responsible for:
- Agent boundary enforcement
- Capability verification and role binding
- Task contract and output contract
- Review gates and escalation policies
- Memory and context policies (v0.2+)

### 2.3 Project Layer

The runtime instance of the protocol.

Responsible for:
- Project goals, directory structure, constraints, and business state machine
- Available agents, skills, tools, and execution environment
- Mapping protocol objects to project tasks
- Executing work and producing results
- Feeding stable methods back to the protocol layer

### 2.4 Agent Layer

Defines a single agent's context, capabilities, skills, memory, and execution habits within a project.

---

## 3. Core Principles

1. **Protocol over role.** Roles are temporary project assignments, not permanent identities.
2. **Capability over name.** Dispatch by declared capability, not by fixed name.
3. **Committee over single brain.** Protocol-layer architecture changes are decided by multi-agent committee, not a single orchestrator.
4. **Project facts over general assumptions.** Committee must read project facts before proposing architectural changes.
5. **Result on disk over message declaration.** Task completion is confirmed by structured results and formal artifacts, not by chat messages.
6. **Method over project specific.** Only cross-project reusable methods, objects, state machines, and governance rules can enter the protocol layer.
7. **Protocol evolvable, always traceable.** Every protocol upgrade must have a proposal, review, decision, activation, and change record.

---

## 4. Abstract Objects

### 4.1 AgentManifest

Declares an agent's current capabilities, not its fixed identity.

```json
{
  "agent_id": "agent-runtime-id",
  "display_name": "optional human name",
  "runtime": {
    "type": "cli | app | api | human | mcp | other",
    "entrypoint": "implementation-defined"
  },
  "capabilities": [
    "architecture_review",
    "code_execution",
    "project_planning",
    "quality_review",
    "document_writing"
  ],
  "limits": {
    "cannot": ["write_production", "access_network"],
    "max_parallel_tasks": 1
  },
  "trust": {
    "level": "experimental | standard | privileged",
    "requires_review": true
  }
}
```

### 4.2 ProjectManifest

Declares how a project adopts the protocol.

```json
{
  "project_id": "example_project",
  "protocol_version": "0.1",
  "project_root": "/path/to/project",
  "runtime_adapter": "file_bus_v1",
  "source_of_truth": ["README.md", "source_of_truth.md"],
  "agents": ["agent-runtime-id-1", "agent-runtime-id-2"],
  "project_roles": {
    "orchestrator": "capability:project_planning",
    "executor": "capability:code_execution",
    "reviewer": "capability:quality_review"
  },
  "validation": {
    "required": true,
    "commands": [],
    "artifacts": []
  }
}
```

### 4.3 ProtocolProposal

A protocol upgrade proposal. Only handles general methods, no project-specific execution content.

```json
{
  "proposal_id": "PP-0001",
  "scope": "protocol_layer",
  "type": "role_model | task_schema | consensus_flow | runtime_contract | verification",
  "problem": "Current protocol cannot express dynamic identities",
  "proposal": "Introduce AgentManifest capabilities field",
  "evidence_refs": ["project://example_project/TASK-0014/result.json"],
  "compatibility": {
    "breaking": false,
    "migration_required": false
  },
  "status": "draft | under_review | accepted | rejected | superseded"
}
```

### 4.4 ArchitectureDecision

A committee-reached architectural decision.

```json
{
  "decision_id": "AD-0001",
  "proposal_id": "PP-0001",
  "decision": "accepted",
  "rationale": "Capability declaration is more reusable than fixed roles across projects",
  "accepted_changes": ["AgentManifest.capabilities"],
  "rejected_changes": [],
  "activation": {
    "protocol_version": "0.2",
    "effective_at": "manual",
    "migration_notes": []
  }
}
```

### 4.5 Task

Tasks are project-layer execution objects. Must follow the protocol's minimum fields.

```json
{
  "task_id": "TASK-0001",
  "layer": "protocol | project | runtime",
  "project_id": "example_project",
  "required_capabilities": ["code_execution"],
  "assigned_agent": "agent-runtime-id",
  "depends_on": [],
  "input_refs": [],
  "output_contract": {
    "required_refs": [],
    "done_condition": "verifiable completion condition"
  },
  "timeout_sec": 1800
}
```

### 4.6 Result

Result is the sole confirmation of task completion.

```json
{
  "task_id": "TASK-0001",
  "status": "done | failed | blocked | timeout | cancelled",
  "summary": "one-line conclusion",
  "output_refs": [],
  "verification_refs": [],
  "error": null,
  "generated_at": "ISO8601"
}
```

---

## 5. Committee Governance

The protocol layer has no single brain. Protocol upgrades are conducted by a committee.

### 5.1 Committee Members

Committee members are not fixed agent names, but capability seats.

| Seat | Capability Required | Responsibility |
|------|-------------------|---------------|
| Architecture | `architecture_review` | Protocol structure stability and reusability |
| Execution | `code_execution` / `workflow_execution` | Implementation feasibility |
| Verification | `quality_review` | Risk, gaps, verification methods |
| Project Context | `project_planning` / `domain_analysis` | Project facts and constraints |

One agent can hold multiple seats, but any proposal requires at least two different agents to participate.

### 5.2 Consensus Flow

```
Project Observation
  → ProtocolProposal
  → Committee Review
  → Objection / Revision
  → ArchitectureDecision
  → Protocol Activation
  → Project Migration
  → Retrospective
```

### 5.3 Acceptance Conditions

- Clear problem identified
- Evidence from project facts or task history
- Abstracted from specific projects
- Not bound to a single model, application, or skill
- Compatibility statement included
- Verification or trial plan included

### 5.4 Rejection Conditions

- Only applicable to a single project
- Just one agent's personal preference
- Depends on an irreplaceable proprietary tool
- No verifiable completion standard
- Breaks current projects with no migration path

---

## 6. Dynamic Identity Model

Agent identity has three components:

```
Runtime Identity + Capability Set + Project Role Binding
```

- **Runtime Identity**: A specific running entity (CLI, App, API, human)
- **Capability Set**: Declared and verified capabilities
- **Project Role Binding**: Temporary role assignment per project/task/phase

No agent has a permanent role. Projects can rebind roles based on capability, availability, risk, and context.

---

## 7. Protocol ↔ Project Interaction

### 7.1 Project Submits Protocol Feedback

Projects that discover general problems can generate `ProtocolProposal`.

### 7.2 Protocol Issues Project Constraints

The protocol layer only imposes general constraints:
- Tasks must have input references
- Results must be structured and written to disk
- Dependencies must be explicitly declared
- Verification must be bound to frozen artifacts
- Protocol upgrades must have decision records

The protocol layer must not impose project-specific conclusions (which content to publish, which script to modify, which directory to use, which business strategy to choose).

---

## 8. Runtime Adapter

The protocol is not bound to a specific communication implementation. Each project connects via a Runtime Adapter.

Available adapters:
- `file_bus_v1`: Shared filesystem (inbox → in_progress → results)
- `http_bus_v1`: HTTP task API
- `queue_bus_v1`: Message queue
- `manual_bus_v1`: Manual task/results copy
- `hybrid_bus_v1`: File + API + notifications

The current recommendation is `file_bus_v1` — simple, auditable, no extra services required.

---

## 9. Versioning & Compatibility

```
MAJOR.MINOR
```

- **MAJOR**: Breaking change
- **MINOR**: Backward-compatible extension

Projects must declare their adopted protocol version in `ProjectManifest.protocol_version`.

Protocol upgrades do not force all projects to migrate. Each project can lock, trial, partially migrate, or declare incompatibility.

---

## 10. Minimum Runnable Loop

```
1. Project declares ProjectManifest
2. Agent declares AgentManifest
3. Project binds temporary roles based on capabilities
4. Project creates Task
5. Runtime Adapter dispatches task
6. Agent executes and writes Result
7. Reviewer verifies Result and output_refs
8. Project captures experience
9. General experience enters ProtocolProposal
10. Committee forms ArchitectureDecision
```
