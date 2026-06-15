# Guarded Upload TaskContract v0.2

> Status: pilot-validated alpha · executable schema and validator available
> Schema: `schemas/guarded_upload_task.schema.json`
> Companion: `schemas/approval_grant.schema.json`
> 负向测试: `protocol/upload-negative-test-matrix-v0.2.md`
> 语义验证器: `tools/validate_guarded_upload_contract.py`

## 1. 设计原则

- **Token 永不进 Contract**：`token_ref` 使用 `secret://` 逻辑引用，由 Runtime 本机 manifest 映射到真实路径。
- **ApprovalGrant 是签名快照**：Runtime 不读取 Project 事实源。Owner 签发 `ApprovalGrant`（绑定 `artifact_sha256 + channel_id + max_privacy + expires_at + source_proof`）后嵌入 Contract，Runtime 即可独立验证。
- **artifact_ref 不可变**：绑定 SHA256 + size + duration，审批后替换文件会被检测。
- **Public 禁止除非审批明确授权**：`max_privacy` 控制上限，`block_public_without_explicit_approval: const true`。
- **execution_host 字段约束**：`enum: ["windows_local_powershell", "mac_durable_runner", "task_scheduler"]`，Agent tool 无法通过 Schema 校验。
- **idempotency_key 防重复上传**：重试前检查同键 receipt，已存在则拒绝。
- **emergency journal**：receipt 写入失败时保留 video_id 和关键信息到独立路径。

## 2. Schema

独立 JSON Schema 位于 `schemas/guarded_upload_task.schema.json`，已接入 TaskContract v0.2 完整性链：

| 继承自 v0.2 | 本 Contract 特有 |
|---|---|
| `task_id`, `project_id`, `application_id` | `task_mode: "guarded_upload"` |
| `required_protocol_version`, `required_capabilities` | `upload_parameters` (artifact_ref + metadata + channel_binding) |
| `context_scope`, `context_expires_at` | `validation_gates` (含 upload 特有 gate) |
| `input_refs`, `redactions` | `approval_grant` (签名快照) |
| `risk_level`, `acceptance_criteria` | `execution_host` (enum 约束) |
| `contract_clarity_score`, `source_proof` | `idempotency_key` (去重) |

**关键约束**：所有嵌套对象 `additionalProperties: false`，禁止 Contract 携带 `oauth_token`、`refresh_token` 等字段。

结构校验之后必须执行语义验证器。Schema 负责字段形状，验证器负责跨字段绑定、有效期、URI 防穿越和审批状态。Runtime 仍需负责解析本地 manifest、校验实际文件哈希、验证 HMAC/签名值以及读取撤销列表；这些环境检查不能由 Schema 替代。

## 3. ApprovalGrant 工作流

```text
Owner (黑灯工厂)
  │
  ├─ 选择成品、频道、公开级别
  ├─ 生成 ApprovalGrant:
  │   approval_id, action=upload,
  │   artifact_sha256, channel_id, max_privacy,
  │   granted_by, granted_at, expires_at,
  │   source_proof (Owner 签名)
  │
  └─ 嵌入 TaskContract → 交给 Runtime

Runtime (Windows node)
  │
  ├─ Schema 校验（Draft202012Validator）
  ├─ 验证 approval_grant:
  │   ├─ revoked != true
  │   ├─ expires_at > now
  │   ├─ artifact_sha256 == upload_parameters.artifact_ref.sha256
  │   ├─ channel_id == upload_parameters.channel_binding.expected_channel_id
  │   └─ max_privacy >= metadata.privacy_status
  ├─ 验证 token (secret:// → manifest 映射 → 文件 → JSON)
  ├─ OAuth: channels.list(mine=true) → 匹配 channel_id
  ├─ 执行上传 (本机 runner)
  └─ 产出 ExecutionReceipt
```

## 4. Token 引用

`token_ref` 只允许 `secret://` 前缀：

```json
{
  "channel_binding": {
    "token_ref": "secret://youtube_oauth_english_drama"
  }
}
```

Runtime 本机 manifest 提供映射：

```json
{
  "secrets": {
    "youtube_oauth_english_drama": "/Users/MY/AgentSecrets/youtube/english-drama.json"
  }
}
```

禁止 `env://`、`local://`、`file://` 等可遍历文件系统的 scheme。

## 5. 执行流程

```text
Phase 0: Schema 校验 (Draft202012Validator)
  ├─ additionalProperties: false → 拦截未声明字段
  ├─ required 检查
  └─ enum/pattern/const 约束

Phase 1: Preflight
  ├─ artifact 存在 + SHA256 匹配 + size ≥10MB
  ├─ metadata 完整
  ├─ approval_grant 有效 (未撤销 + 未过期 + 匹配)
  ├─ token_ref → manifest 映射 → 文件存在
  └─ execution_host 允许 + idempotency_key 唯一

Phase 2: OAuth
  ├─ token 解析 → credentials
  ├─ channels.list(mine=true)
  └─ channel_id 匹配

Phase 3: 上传
  ├─ 检查本地日配额
  ├─ youtube_upload.py (本机 runner, 非 Agent tool)
  └─ UPLOAD=true

Phase 4: 后验证
  ├─ video_id 已返回
  ├─ privacy 状态匹配
  └─ receipt 写入 (失败则 emergency journal)
```

## 6. Guard 规则速查

| Guard | 级别 | 阶段 |
|---|---|---|
| `ARTIFACT_NOT_FOUND` | P0 | Preflight |
| `ARTIFACT_SHA256_MISMATCH` | P0 | Preflight |
| `ARTIFACT_TOO_SMALL` | P0 | Preflight |
| `TOKEN_UNRESOLVABLE` | P0 | Preflight |
| `TOKEN_FILE_MISSING` | P0 | Preflight |
| `TOKEN_INVALID_JSON` | P0 | Preflight |
| `METADATA_INCOMPLETE` | P0 | Schema |
| `PUBLIC_EXCEEDS_MAX_PRIVACY` | P0 | Preflight |
| `APPROVAL_MISSING_OR_INVALID` | P0 | Preflight |
| `APPROVAL_REVOKED` | P0 | Preflight |
| `APPROVAL_EXPIRED` | P0 | Preflight |
| `CHANNEL_ID_PLACEHOLDER` | P0 | Schema |
| `EXECUTION_HOST_INVALID` | P0 | Schema |
| `ADDITIONAL_PROPERTIES_DETECTED` | P0 | Schema |
| `DUPLICATE_IDEMPOTENCY_KEY` | P0 | Preflight |
| `CHANNEL_ID_MISMATCH` | P0 | OAuth |
| `OAUTH_SCOPE_INSUFFICIENT` | P0 | OAuth |
| `TOKEN_EXPIRED` | P1 | OAuth |
| `THUMBNAIL_MISSING` | P2 | Preflight |
| `RECEIPT_DIR_UNWRITABLE` | P1 | Post |
| `LOCAL_QUOTA_EXHAUSTED` | P1 | Preflight |
