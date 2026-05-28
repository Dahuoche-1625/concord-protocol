# Concord Protocol v0.1-alpha

> 文件驱动多 Agent 协作的最小可执行安全内核。

**这是一份早期草案 (v0.1-alpha)，不是成熟标准。** 它为共享工作区中的每个 Agent 回答三个问题：

1. **你是谁？** — `AgentIdentity`
2. **你能做什么？** — `CapabilityRecord` + `AgentBoundary`
3. **你怎么证明没有越界？** — `RuntimeGuard` + `AuditLog`

## 这是什么

一套让多个 AI Agent 在共享文件系统中协作的协议。每个 Agent 声明自己的身份、能力和写入边界。`file_bus_guard` 在任务执行前后验证 Agent 没有写入越界文件。

## 这不是什么

- ❌ 沙箱或容器 — V0.1 是 `verify_only` 模式。能发现和阻断结果生效，但**不阻止** Agent 实际写入或读取文件。
- ❌ 通用 Agent 框架 — V0.1 只是**安全内核**。角色绑定、上下文策略、skill 管理、审查门禁、审批流程延后到 v0.2+。
- ❌ 完整的 Agent 解决方案 — 你自带 Agent、skills、任务队列、业务逻辑。这个协议只加安全层。

## 阅读顺序

1. [`protocol/reusable-multi-agent-protocol-v0.1.md`](protocol/reusable-multi-agent-protocol-v0.1.md) — 四层模型、能力驱动角色、委员会治理。
2. [`framework/framework-security-kernel-v0.1.md`](framework/framework-security-kernel-v0.1.md) — 6 个核心对象 + 2 个执行机制，你需要实际实现的部分。
3. [`reference/file_bus_guard_v0.md`](reference/file_bus_guard_v0.md) — 参考实现伪代码。
4. [`examples/minimal_project/`](examples/minimal_project/) — 一个最小两 Agent 示例项目。

## 核心模型

```
Protocol Layer     → 通用协作方法
Framework Layer    → Agent 边界、能力、权限（本协议的核心）
Project Layer      → 项目事实、目标、业务状态机
Agent Layer        → 单个 Agent 的上下文、skills、记忆
```

## 版本

- **v0.1-alpha** — 安全内核。`verify_only` 模式。6 对象 + RuntimeGuard + AuditLog。
- **v0.2** (计划中) — 角色绑定、上下文策略、enforced 沙箱、审查门禁。

## License

Apache-2.0。包含专利授权条款，适合协议/框架类项目。

## 关于命名

**Concord** = 共识、协调、一致。映射多 Agent 委员会先达成架构共识、再进入项目执行的核心流程。

---

[English version](README.md)
