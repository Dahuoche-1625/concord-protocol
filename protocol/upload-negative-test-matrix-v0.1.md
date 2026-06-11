# Upload Guarded Verify — 负向测试矩阵 v0.1

> 目标：在 prod upload 之前跑完所有已知失败路径，确保每一个 guard 规则都有对应测试。

## 测试矩阵

| # | Guard 规则 | 测试输入 | 预期输出 | 严重性 |
|---|---|---|---|---|
| NT-01 | `VIDEO_MISSING` | `video_path` 指向不存在的文件 | `FAIL video not found`，不发起 API 调用 | P0 |
| NT-02 | `VIDEO_TOO_SMALL` | video_path 指向 `<10MB` 的 test.mp4 | `FAIL video too small`，不发起上传 | P0 |
| NT-03 | `TOKEN_UNRESOLVABLE` | `token_ref: "env://NONEXISTENT_VAR"` | `FAIL token unresolvable`，不发 API | P0 |
| NT-04 | `TOKEN_FILE_MISSING` | `token_ref: "local:///nonexistent/token.json"` | `FAIL token file not found` | P0 |
| NT-05 | `TOKEN_INVALID_JSON` | token 文件内容为 `{malformed` | `FAIL token parse error` | P0 |
| NT-06 | `METADATA_TITLE_EMPTY` | `metadata.title: ""` | `FAIL title is required` | P0 |
| NT-07 | `METADATA_DESC_EMPTY` | `metadata.description: ""` | `FAIL description is required` | P0 |
| NT-08 | `PUBLIC_WITHOUT_APPROVAL` | `privacy_status: "public"`, `owner_approval_id` 缺失 | `FAIL public requires owner approval` | P0 |
| NT-09 | `CHANNEL_ID_MISMATCH` | token 属于 `UC_OTHER_123`，Contract 声明 `UC_EXPECTED_456` | `FAIL channel mismatch: expected UC_EXPECTED_456, got UC_OTHER_123` | P0 |
| NT-10 | `CHANNEL_ID_PLACEHOLDER` | `expected_channel_id: "FILL_BEFORE_UPLOAD"` | `FAIL channel id is a placeholder` | P0 |
| NT-11 | `OAUTH_SCOPE_INSUFFICIENT` | token 无 `https://www.googleapis.com/auth/youtube.upload` scope | `FAIL oauth scope missing youtube.upload` | P0 |
| NT-12 | `TOKEN_EXPIRED` | token 的 `expiry` 已过期且 refresh_token 不可用 | `FAIL token expired and not refreshable` | P0 |
| NT-13 | `OWNER_APPROVAL_MISSING` | `validation_gates.owner_approval_id` 指向不存在的审批 | `FAIL owner approval not found` | P0 |
| NT-14 | `OWNER_APPROVAL_REVOKED` | approval record `status: "revoked"` | `FAIL owner approval has been revoked` | P0 |
| NT-15 | `RECEIPT_DIR_UNWRITABLE` | `receipt_output_dir` 指向无写权限的目录 | `FAIL receipt output dir unwritable` | P1 |
| NT-16 | `THUMBNAIL_MISSING` (warning) | `thumbnail_path` 指向不存在的文件 | `WARN thumbnail missing, continuing upload` | P1 |
| NT-17 | `THUMBNAIL_INVALID_FORMAT` | thumbnail 是 `.webp`（YouTube 不支持） | `WARN thumbnail format may be unsupported` | P2 |
| NT-18 | `TAGS_EXCEED_LIMIT` | `metadata.tags` 超过 30 个 | `WARN tags exceed limit, truncating` | P2 |
| NT-19 | `TITLE_EXCEED_LENGTH` | `metadata.title` 超过 100 字符 | `WARN title truncated to 100 chars` | P2 |
| NT-20 | `CONTRACT_REDACTIONS_VIOLATED` | Contract 包含 `oauth_token` 字段（在 redactions 列表中） | `FAIL contract contains redacted field` | P0 |
| NT-21 | `AGENT_TOOL_UPLOAD_ATTEMPTED` | 上传调用的 `execution_host` 不是本机 runner/Task Scheduler | `FAIL upload must use local runner, not agent tool` | P0 |
| NT-22 | `CONTEXT_ISOLATION_VIOLATED` | Runtime 尝试读取 `04_CONTENT_LIBRARY/production_state.json` | `FAIL context isolation violated` | P0 |

## 测试环境要求

| 要求 | 说明 |
|---|---|
| 测试 token | 使用一个仅有 youtube.upload scope 的 disposable test token |
| 测试频道 | 专用 test channel（不承载任何生产视频） |
| 测试视频 | 使用 Wave 5 验收时生成的 `N001-final.mp4` (158MB) |
| 负向视频 | 生成一个 `<10MB` 的 dummy.mp4 用于 NT-02 |
| 不存在的路径 | `external://deployment/output/NONEXISTENT/nope.mp4` |
| runtime_root | `$HOME/DramaPOC` 或等效路径 |

## 执行顺序

```text
Phase 0: 环境准备（token + test channel + 测试视频）
Phase 1: Preflight 负向测试 (NT-01 ~ NT-08, NT-10, NT-15 ~ NT-19)
  不发起任何 YouTube API 调用。
Phase 2: OAuth 负向测试 (NT-09, NT-11, NT-12)
  需要 disposable test token。
Phase 3: 审批负向测试 (NT-13, NT-14)
  需要 mock approval record。
Phase 4: 契约完整性测试 (NT-20, NT-21, NT-22)
  不依赖 token 或网络。
Phase 5: Private upload smoke test
  所有 NT 通过后，用真实 test token + test channel 跑一次完整上传。
```

## 验收标准

- 所有 P0 测试（14 项）必须 PASS
- 所有 P1/P2 测试（8 项）必须 PASS 或记录为已知限制
- NT-21（Agent tool 禁止上传）在 Windows Task Scheduler 承载的上传中也必须通过
- Private smoke test 产生的 YouTube video ID 可在 YouTube Studio 中确认
- ExecutionReceipt 包含正确的 video ID、privacy 状态、上传时间戳
