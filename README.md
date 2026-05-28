# Concord Protocol v0.1-alpha

[中文版](README.zh-CN.md)

> A minimal executable security kernel for file-driven multi-agent collaboration.

**This is an early draft (v0.1-alpha), not a mature standard.** It answers three questions for every agent in a shared workspace:

1. **Who are you?** — `AgentIdentity`
2. **What can you do?** — `CapabilityRecord` + `AgentBoundary`
3. **How do you prove you stayed within bounds?** — `RuntimeGuard` + `AuditLog`

## What this is

A protocol for multiple AI agents to collaborate in a shared filesystem workspace without a central orchestrator. Each agent declares its identity, capabilities, and write boundaries. A `file_bus_guard` verifies before and after each task that the agent didn't write outside its allowed scope.

## What this is NOT

- ❌ A sandbox or container — V0.1 is `verify_only`. It detects and blocks result acceptance, but does **not** prevent file writes or reads at the OS level.
- ❌ A general-purpose agent framework — V0.1 is a **security kernel only**. Role binding, context policies, skill management, review gates, and approval workflows are deferred to v0.2+.
- ❌ A complete multi-agent solution — You bring your own agents, skills, task queues, and business logic. This protocol adds the security layer.

## Structure

```
├── README.md
├── LICENSE                          (Apache-2.0)
├── SECURITY.md                      (known limitations, security model)
├── GOVERNANCE.md                    (how the protocol evolves)
├── protocol/
│   └── reusable-multi-agent-protocol-v0.1.md
├── framework/
│   ├── framework-security-kernel-v0.1.md   (V0.1 execution target — 6 objects)
│   └── framework-extended-draft.md         (full 11-object design reference)
├── schemas/                         (JSON Schema for each object)
├── reference/
│   └── file_bus_guard_v0.md         (reference implementation guide)
└── examples/
    └── minimal_project/             (minimal working example)
```

## Quick start

Read in this order:

1. [`protocol/reusable-multi-agent-protocol-v0.1.md`](protocol/reusable-multi-agent-protocol-v0.1.md) — Four-layer model, capability-driven roles, committee governance.
2. [`framework/framework-security-kernel-v0.1.md`](framework/framework-security-kernel-v0.1.md) — The 6 core objects + 2 execution mechanisms you actually implement.
3. [`reference/file_bus_guard_v0.md`](reference/file_bus_guard_v0.md) — Reference implementation pseudocode.
4. [`examples/minimal_project/`](examples/minimal_project/) — A minimal two-agent project showing the protocol in action.

## Version

- **v0.1-alpha** — Security kernel. `verify_only` mode. 6 objects + RuntimeGuard + AuditLog.
- **v0.2** (planned) — Role binding, context policies, enforced sandbox mode, review gates.

## License

Apache-2.0. See [LICENSE](LICENSE).

## Why not MIT?

Apache-2.0 includes an explicit patent grant, which is important for a protocol/framework that others may implement commercially. If someone contributes a novel verification method, the patent grant ensures all implementors can use it.
