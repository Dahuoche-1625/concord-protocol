# Guarded Upload TaskContract v0.1

> Status: draft · Wave 7 pre-design
> 目标：定义 YouTube 上传行为的安全契约。Runtime 执行上传，Project 控制授权。Token 和频道绑定不得出现在 Contract 正文中。

## 1. 设计原则

- **Token 永不进 Contract**：`token_ref` 仅表达"由哪个环境变量/Keychain 解析"，不做值传递。
- **频道绑定由 Project 声明，Runtime 验证**：`expected_channel_id` 必须在 OAuth token 授权返回的 channel_id 中匹配。
- **Owner 审批前置**：没有 `owner_approval_id` 的 TaskContract 拒绝执行。
- **Upload 是最小权限动作**：一个 Contract 只绑定一个视频文件 + 一个频道。
- **Runtime 不读飞书事实源**：不查频道表、不查审批表、不查剧目库。

## 2. Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://concord-protocol.dev/schemas/guarded_upload_task_v0.1",
  "title": "Guarded Upload TaskContract",
  "type": "object",
  "required": [
    "task_id", "task_mode", "required_protocol_version",
    "required_capabilities", "upload_parameters", "validation_gates"
  ],
  "properties": {
    "task_id": {
      "type": "string",
      "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]{2,79}$"
    },
    "task_mode": {
      "type": "string",
      "const": "guarded_upload"
    },
    "project_id": {
      "type": "string"
    },
    "application_id": {
      "type": "string"
    },
    "required_protocol_version": {
      "type": "string",
      "const": "0.2"
    },
    "required_capabilities": {
      "type": "array",
      "items": { "type": "string" },
      "contains": { "const": "youtube_api_upload_capable" }
    },
    "risk_level": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"]
    },
    "context_scope": {
      "type": "string",
      "const": "upload_only"
    },
    "redactions": {
      "type": "array",
      "items": { "type": "string" },
      "contains": { "const": "oauth_token" }
    },
    "upload_parameters": {
      "type": "object",
      "required": ["video_path", "metadata", "channel_binding"],
      "properties": {
        "video_path": {
          "type": "string",
          "description": "解析为 external://deployment/output/ 路径，Runtime 必须验证文件存在且大小 >10MB"
        },
        "metadata": {
          "type": "object",
          "required": ["title", "description", "privacy_status"],
          "properties": {
            "title": { "type": "string", "minLength": 1, "maxLength": 100 },
            "description": { "type": "string", "maxLength": 5000 },
            "tags": {
              "type": "array",
              "items": { "type": "string" },
              "maxItems": 30
            },
            "category_id": { "type": "integer", "minimum": 1, "maximum": 44 },
            "privacy_status": {
              "type": "string",
              "enum": ["private", "unlisted", "public"]
            },
            "thumbnail_path": { "type": "string" },
            "language": { "type": "string", "minLength": 2, "maxLength": 5 }
          }
        },
        "channel_binding": {
          "type": "object",
          "required": ["channel_key", "expected_channel_id", "token_ref"],
          "properties": {
            "channel_key": {
              "type": "string",
              "description": "Project channel key，用于 receipt prefix 和日志，不用于频道查找"
            },
            "expected_channel_id": {
              "type": "string",
              "pattern": "^UC[A-Za-z0-9_-]{22}$",
              "description": "YouTube channel ID，Runtime 必须与 OAuth token 返回的 channel_id 匹配"
            },
            "token_ref": {
              "type": "string",
              "pattern": "^(env|keychain|local)://",
              "description": "token 位置引用，不是 token 值。Runtime 解析后执行 OAuth 验证"
            }
          }
        },
        "receipt_config": {
          "type": "object",
          "properties": {
            "receipt_prefix": { "type": "string" },
            "receipt_output_dir": { "type": "string" }
          }
        }
      }
    },
    "validation_gates": {
      "type": "object",
      "required": [
        "require_owner_approval", "require_expected_channel_id_match",
        "require_token_existence", "require_receipt_on_completion"
      ],
      "properties": {
        "require_owner_approval": { "type": "boolean", "const": true },
        "owner_approval_id": { "type": "string" },
        "require_expected_channel_id_match": { "type": "boolean", "const": true },
        "require_token_existence": { "type": "boolean", "const": true },
        "require_metadata_completeness": { "type": "boolean" },
        "block_public_without_explicit_approval": { "type": "boolean" },
        "block_unknown_channel": { "type": "boolean", "const": true },
        "max_retries": { "type": "integer", "minimum": 0, "maximum": 3 },
        "require_receipt_on_completion": { "type": "boolean", "const": true }
      }
    }
  }
}
```

## 3. 执行流程

```text
Project (blacklight-factory)
  │
  ├─ Owner 审批 → APPROVAL-RECORD
  ├─ 生成 guarded_upload TaskContract
  │   ├─ video_path
  │   ├─ metadata (title / description / tags / privacy)
  │   ├─ channel_binding (channel_key / expected_channel_id / token_ref)
  │   └─ validation_gates (owner_approval_id + gates)
  │
  └─ Runtime Release adapter → TaskDispatch → Windows node

Runtime (Windows node)
  │
  ├─ Preflight 检查
  │   ├─ ✅ video 存在且 >10MB
  │   ├─ ✅ metadata 完整（title/description 非空）
  │   ├─ ✅ token_ref 可解析且文件存在
  │   ├─ ✅ privacy_status 非 public 或有显式批准
  │   └─ ✅ 频道不是 unknown/protected
  │
  ├─ OAuth 验证
  │   ├─ 从 token_ref 加载 OAuth credentials
  │   ├─ 调用 YouTube API channels.list(mine=true)
  │   ├─ ✅ 返回的 channel_id == expected_channel_id
  │   └─ ❌ 不匹配 → FAIL，不发起上传
  │
  ├─ 执行上传
  │   ├─ youtube_upload.py (本机 runner，非 Agent tool)
  │   └─ UPLOAD=true（仅此 action 允许）
  │
  ├─ 后验证
  │   ├─ YouTube video ID 已返回
  │   ├─ privacy 状态与 Contract 一致
  │   └─ 可访问（public 或 token-scoped private）
  │
  └─ 产出 ExecutionReceipt → ReviewResult
```

## 4. Guard 规则（upload-specific）

| Guard | 检查时机 | 失败动作 |
|---|---|---|
| `VIDEO_MISSING` | preflight | 拒绝，返回错误原因 |
| `VIDEO_TOO_SMALL` | preflight | 拒绝（<10MB 几乎不可能是完整成片） |
| `TOKEN_UNRESOLVABLE` | preflight | 拒绝，不发起任何 API 调用 |
| `METADATA_INCOMPLETE` | preflight | 拒绝（title/description 不可为空） |
| `PUBLIC_WITHOUT_APPROVAL` | preflight | 拒绝（除非 validation_gates 显式允许） |
| `CHANNEL_ID_MISMATCH` | OAuth | 拒绝，token 与声明的频道不一致 |
| `OAUTH_SCOPE_INSUFFICIENT` | OAuth | 拒绝，token 缺少 youtube.upload 权限 |
| `UPLOAD_QUOTA_EXHAUSTED` | 执行前 | 拒绝并返回 quota 状态 |
| `UPLOAD_NETWORK_FAILURE` | 执行中 | 重试（最多 max_retries 次） |
| `RECEIPT_WRITE_FAILED` | 完成后 | 标记 partial_success，保留视频 ID |
| `PRIVACY_NOT_CONFIRMED` | 后验证 | warning，标记 receipt |
| `THUMBNAIL_MISSING` | preflight | warning，继续上传（封面可选） |

## 5. Guard 规则（复用通用 Bridge Guard）

以下规则从 `guarded_verify_v0.2.json` 继承，不需在 Contract 中重复声明：

- `CONTEXT_ISOLATION`：Runtime 不读取 Project 事实源
- `WRITE_ROOT_ENFORCEMENT`：上传产出只写入 `allowed_write_roots`
- `ATOMIC_RECEIPT`：receipt 必须原子写入
- `EXIT_CODE_CONTRACT`：上传成功后 `result.json.status == done`
- `TOOL_VERSION_RECORD`：receipt 包含 ffmpeg/ffprobe/Python 版本

## 6. 禁止事项

- ❌ TaskContract 包含 `oauth_token`、`client_secret`、`refresh_token` 或其值
- ❌ Token 以 base64/加密形式写入 Contract
- ❌ `privacy_status: "public"` 在没有显式 `owner_approval_id` 的情况下
- ❌ `expected_channel_id` 为空或占位符
- ❌ Runtime 自行修改 metadata 或 channel_binding
- ❌ Agent tool 直接承载上传进程（必须通过本机 runner/Task Scheduler）
