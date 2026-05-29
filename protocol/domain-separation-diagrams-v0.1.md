# Domain Separation Diagrams v0.1

> Visual companion for [Domain Separation Model v0.1](domain-separation-model-v0.1.md).

---

## 1. Architecture Overview

```mermaid
flowchart TB
  subgraph Shared["Shared Layers"]
    Protocol["Protocol Layer<br/>collaboration rules, governance, object semantics"]
    Framework["Framework Layer<br/>identity, boundary, capability, guard, audit"]
    Application["Application Layer<br/>reusable workflow templates and skill profiles"]
    Protocol --> Framework --> Application
  end

  subgraph Project["Project Domain<br/>business intent and facts"]
    ProjectConfig["project config<br/>policies, source refs, approvals"]
    ProjectState["project state<br/>business objects, schedules, acceptance criteria"]
  end

  subgraph Bridge["Bridge Layer<br/>contract-only cross-domain interface"]
    TaskContract["TaskContract"]
    TaskDispatch["TaskDispatch"]
    TaskLease["TaskLease"]
    ExecutionReceipt["ExecutionReceipt"]
    ReviewResult["ReviewResult"]
  end

  subgraph Runtime["Runtime Mesh Domain<br/>execution capacity and state"]
    Coordinator["Coordinator Agent<br/>publish and summarize only"]
    WorkerA["Worker Agent A"]
    WorkerB["Worker Agent B"]
    NodeRegistry["node registry<br/>heartbeat, capabilities, leases"]
  end

  Application --> Project
  Application --> Runtime

  ProjectConfig --> TaskContract
  ProjectState --> TaskContract
  TaskContract --> TaskDispatch
  TaskDispatch --> Coordinator
  Coordinator --> TaskLease
  TaskLease --> WorkerA
  TaskLease --> WorkerB
  WorkerA --> ExecutionReceipt
  WorkerB --> ExecutionReceipt
  ExecutionReceipt --> ReviewResult
  ReviewResult --> ProjectState

  Runtime -.->|MUST NOT directly read project facts| Project
  Project -.->|MUST NOT directly invoke agents| Runtime
```

---

## 2. Cross-Domain Task Flow

```mermaid
sequenceDiagram
  autonumber
  participant Project as Project Domain
  participant Bridge as Bridge Layer
  participant Coord as Coordinator Agent
  participant Worker as Worker Agent
  participant Guard as RuntimeGuard
  participant Review as Reviewer

  Project->>Bridge: create TaskContract<br/>minimum project context only
  Coord->>Bridge: publish TaskDispatch<br/>with project authority
  Worker->>Bridge: claim TaskLease atomically
  Bridge-->>Worker: lease_id + task snapshot
  Worker->>Worker: execute locally
  Worker->>Guard: submit result + artifact_refs
  Guard->>Guard: boundary, output, source_refs checks
  Guard->>Bridge: write ExecutionReceipt
  Bridge->>Review: expose receipt for review
  Review->>Bridge: write ReviewResult
  Bridge-->>Project: accepted / rejected / retry / escalated
```

---

## 3. Many-to-Many Project Runtime Binding

```mermaid
flowchart LR
  subgraph Projects["Project Domains"]
    P1["Project A"]
    P2["Project B"]
    P3["Project C"]
  end

  subgraph Contracts["Bridge Objects<br/>temporary task bindings"]
    C1["TaskContract A-1"]
    C2["TaskContract A-2"]
    C3["TaskContract B-1"]
    C4["TaskContract C-1"]
  end

  subgraph Meshes["Runtime Mesh Domains"]
    M1["Runtime Mesh 1<br/>Mac / local agents"]
    M2["Runtime Mesh 2<br/>Windows / worker agents"]
    M3["Runtime Mesh 3<br/>cloud or future adapter"]
  end

  P1 --> C1 --> M1
  P1 --> C2 --> M2
  P2 --> C3 --> M1
  P3 --> C4 --> M3

  C1 -.->|binding ends when task closes| C1
  C2 -.->|binding ends when task closes| C2
```

---

## 4. Task Lifecycle

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> dispatched
  dispatched --> claimed
  dispatched --> cancelled
  claimed --> running
  claimed --> expired
  claimed --> cancelled
  running --> partial_done
  running --> done
  running --> failed
  running --> expired
  running --> invalid
  running --> cancelled
  partial_done --> dispatched: retry / continue
  partial_done --> reviewed
  done --> reviewed
  failed --> dispatched: retry
  failed --> reviewed
  expired --> dispatched: reclaim
  cancelled --> reviewed
  invalid --> reviewed
  reviewed --> [*]
```

---

## 5. Bridge Object Authority

```mermaid
flowchart TB
  Human["Project-authorized human / owner"]
  ProjectAgent["Project-authorized agent"]
  Coordinator["Coordinator Agent<br/>runtime role with project authority"]
  Worker["Worker Agent<br/>active lease holder"]
  Reviewer["Reviewer / review agent / approval adapter"]

  TaskContract["TaskContract"]
  TaskDispatch["TaskDispatch"]
  TaskLease["TaskLease"]
  ExecutionReceipt["ExecutionReceipt"]
  ReviewResult["ReviewResult"]

  Human --> TaskContract
  ProjectAgent --> TaskContract
  Coordinator --> TaskDispatch
  Worker --> TaskLease
  Worker --> ExecutionReceipt
  Reviewer --> ReviewResult
  Human --> ReviewResult

  TaskContract --> TaskDispatch --> TaskLease --> ExecutionReceipt --> ReviewResult
```

---

## 6. TaskContract to Lease Binding

```mermaid
flowchart LR
  Project["Project Domain<br/>business intent"]
  Contract["TaskContract<br/>required_capabilities<br/>context_scope<br/>input_refs<br/>output_contract_ref"]
  Dispatch["TaskDispatch<br/>target_mesh<br/>dispatch_policy"]
  Lease["TaskLease<br/>agent_id + node_id<br/>lease_until"]
  Worker["Worker Agent<br/>local execution"]

  Project --> Contract
  Contract --> Dispatch
  Dispatch --> Lease
  Lease --> Worker

  Contract -.->|distributed mode: assigned_agent is null| Dispatch
  Lease -.->|claim binds concrete worker| Contract
```

---

## 7. Security Kernel Relationship

```mermaid
flowchart LR
  Task["Bridge Object<br/>TaskContract / Lease / Receipt"]
  DomainCheck["Domain Separation Check<br/>authorized, minimal, auditable, contract-based"]
  KernelCheck["Framework Security Kernel Check<br/>identity, capability, boundary, RuntimeGuard"]
  Accept["Result can be accepted"]
  Reject["Reject / invalid / review required"]

  Task --> DomainCheck
  DomainCheck -->|pass| KernelCheck
  DomainCheck -->|fail| Reject
  KernelCheck -->|pass| Accept
  KernelCheck -->|fail| Reject
```
