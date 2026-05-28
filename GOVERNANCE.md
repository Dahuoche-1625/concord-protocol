# Governance — Agent Protocol

## How the protocol evolves

The Agent Protocol uses a **multi-seat committee model**. Protocol-level changes (new objects, breaking schema changes, security model changes) require committee review and consensus.

### Committee seats

| Seat | Responsibility | Required capability |
|------|---------------|-------------------|
| Architecture | Protocol structure stability, schema consistency, backward compatibility | `architecture_review` |
| Execution | Implementation feasibility, runtime integration, migration cost | `workflow_execution` |
| Verification | Security gaps, risk assessment, threat model, state machine correctness | `quality_review` |
| Project Context | Real-world use case validation, operational modeling | `project_planning` |

A single agent may hold multiple seats, but any protocol proposal requires at least **two different agents** to participate in review.

### Proposal lifecycle

```
Observation (from any project using the protocol)
  → ProtocolProposal (submitted to committee)
  → Committee Review (all seats evaluate)
  → Objection / Revision (address concerns)
  → ArchitectureDecision (accepted / rejected / deferred)
  → Protocol Activation (version bump + migration notes)
  → Implementation Migration (projects upgrade on their own schedule)
```

### Acceptance criteria

A protocol proposal must satisfy ALL of:

- Identifies a real problem with project evidence
- Abstracted from specific projects, not tied to a single project's needs
- Not bound to a specific agent implementation, model, tool, or skill
- Has a compatibility statement (breaking vs non-breaking)
- Has a verification plan or trial run proposal

### Rejection criteria

A proposal is rejected if ANY of:

- Only applies to a single project or agent
- Depends on a specific proprietary tool
- Has no verifiable completion criteria
- Breaks current projects with no migration path

### Versioning

```
MAJOR.MINOR
```

- **MAJOR**: Breaking changes (schema changes that require migration)
- **MINOR**: Backward-compatible additions (new optional fields, new objects)

Projects declare their adopted protocol version in `framework_manifest.json`. Protocol upgrades never force all projects to migrate simultaneously.

### Current version

- **v0.1-alpha**: Security kernel. 6 objects. `verify_only` mode. Discussion draft.
- **v0.2** (planned): Role binding, context policies, enforced sandbox, review gates.

### How to participate

1. Implement the protocol in your project.
2. Document your experience — what worked, what broke, what's missing.
3. Submit a ProtocolProposal with evidence from your project.
4. Participate in committee review.

This is not a corporate governance document. It's how the protocol itself stays honest.
