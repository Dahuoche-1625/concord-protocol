# Concord Protocol v0.1-alpha

[中文版](README.zh-CN.md)

> A minimal executable security kernel for file-driven multi-agent collaboration.

**This is an early draft (v0.1-alpha), not a mature standard.** It answers three questions for every agent in a shared workspace:

1. **Who are you?** — `AgentIdentity`
2. **What can you do?** — `CapabilityRecord` + `AgentBoundary`
3. **How do you prove you stayed within bounds?** — `RuntimeGuard` + `AuditLog`
4. **How do projects and runtimes stay decoupled?** — `Domain Separation Model` + Bridge Objects

## What this is

A protocol for multiple AI agents to collaborate in shared or distributed workspaces without a central super-agent. Each agent declares its identity, capabilities, and write boundaries. A `file_bus_guard` verifies before and after each task that the agent didn't write outside its allowed scope. The domain separation model keeps project facts and runtime execution state isolated, connected only through bridge objects such as `TaskContract`, `TaskLease`, and `ExecutionReceipt`.

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
│   ├── reusable-multi-agent-protocol-v0.1.md
│   ├── domain-separation-model-v0.1.md      (Project/Runtime isolation + Bridge Objects)
│   └── domain-separation-diagrams-v0.1.md   (Mermaid diagrams)
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
3. [`protocol/domain-separation-model-v0.1.md`](protocol/domain-separation-model-v0.1.md) — Project/Runtime isolation, distributed task bridge objects, leases, and receipts.
4. [`protocol/domain-separation-diagrams-v0.1.md`](protocol/domain-separation-diagrams-v0.1.md) — Mermaid diagrams for the domain separation architecture.
5. [`reference/file_bus_guard_v0.md`](reference/file_bus_guard_v0.md) — Reference implementation pseudocode.
6. [`examples/minimal_project/`](examples/minimal_project/) — A minimal two-agent project showing the protocol in action.

## Version

- **v0.1-alpha** — Security kernel + domain separation draft. `verify_only` mode. 6 security objects + RuntimeGuard + AuditLog + Bridge Object model.
- **v0.2** (planned) — Main protocol model consolidation, Task schema split, role binding, context policies, enforced sandbox mode, review gates, transport adapter schemas.

## License

Apache-2.0. See [LICENSE](LICENSE).

## Why not MIT?

Apache-2.0 includes an explicit patent grant, which is important for a protocol/framework that others may implement commercially. If someone contributes a novel verification method, the patent grant ensures all implementors can use it.
