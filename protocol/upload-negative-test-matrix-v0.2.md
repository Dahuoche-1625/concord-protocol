# Upload Guarded Verify — 负向测试矩阵 v0.2

> 对应 Schema: `schemas/guarded_upload_task.schema.json` v0.2
> 对应 ApprovalGrant: `schemas/approval_grant.schema.json` v0.1
> 19 P0 / 5 P1 / 1 P2 / 2 smoke，共 27 项

## Phase 1: Preflight — 不发起 YouTube API

| # | Guard | 测试输入 | 预期 | 级别 |
|---|---|---|---|---|
| NT-01 | `artifact_ref.path` 不存在 | path 指向不存在的文件 | `FAIL artifact not found`, 不发起 API | P0 |
| NT-02 | `artifact_ref.sha256` 不匹配 | sha256 ≠ 文件实际哈希 | `FAIL artifact sha256 mismatch` | P0 |
| NT-03 | `artifact_ref.size_bytes` <10MB | size_bytes=5000000 | `FAIL artifact too small` | P0 |
| NT-04 | `token_ref` 非法格式 | `token_ref: "env://VAR"` | Schema 拒绝（pattern: `^secret://`） | P0 |
| NT-05 | `secret://` 映射缺失 | manifest 无对应 secret entry | `FAIL secret unresolved: xxxxx` | P0 |
| NT-06 | token 文件不存在 | secret 映射到不存在文件 | `FAIL token file not found` | P0 |
| NT-07 | token JSON 格式错误 | 内容 `{malformed` | `FAIL token parse error` | P0 |
| NT-08 | `metadata.title` 为空 | `title: ""` | Schema 拒绝（minLength:1） | P0 |
| NT-09 | `metadata.description` 为空 | `description: ""` | Schema 拒绝（minLength:1） | P0 |
| NT-10 | 无审批尝试 public | `privacy: "public"`, `max_privacy: "private"` | `FAIL public exceeds approved max_privacy: private` | P0 |
| NT-11 | 无 approval_grant | 整个 `approval_grant` 字段缺失 | Schema 拒绝（required） | P0 |
| NT-12 | approval_grant 已撤销 | `revoked: true` | `FAIL approval has been revoked` | P0 |
| NT-13 | approval_grant 已过期 | `expires_at` 早于当前时间 | `FAIL approval has expired` | P0 |
| NT-14 | `channel_id` 占位符 | `expected_channel_id: "FILL_BEFORE_UPLOAD"` | Schema 拒绝（pattern 不匹配） | P0 |
| NT-15 | `execution_host` 不在允许列表 | `execution_host: "agent_tool"` | Schema 拒绝（enum） | P0 |
| NT-16 | `additionalProperties` 泄漏 token | Contract 含 `oauth_token: "ya29.xxx"` | Schema 拒绝（additionalProperties:false） | P0 |
| NT-17 | `idempotency_key` 重复 | 同键的 receipt 已存在 | `FAIL duplicate idempotency_key; prior receipt found` | P0 |

## Phase 2: OAuth — 需要 disposable test token

| # | Guard | 测试输入 | 预期 | 级别 |
|---|---|---|---|---|
| NT-18 | channel_id 不匹配 | token 属 `UCAbCdEfGhIjKlMnOpQrStUv`，contract 声明 `UCXyZxYzXyZxYzXyZxYzXyZxY` | `FAIL channel mismatch` | P0 |
| NT-19 | OAuth scope 不足 | token 无 `youtube.upload` | `FAIL oauth scope insufficient` | P0 |
| NT-20 | token 过期且无 refresh | expiry 已过，refresh_token 无效 | `FAIL token expired, cannot refresh` | P1 |

## Phase 3: 契约完整性

| # | Guard | 测试输入 | 预期 | 级别 |
|---|---|---|---|---|
| NT-21 | `context_expires_at` 缺失 | 字段缺失 | Schema 拒绝（required） | P1 |
| NT-22 | `contract_clarity_score` <3 | clarity_score=2 | Schema 拒绝（minimum:3） | P1 |

## Phase 4: 执行期

| # | Guard | 测试输入 | 预期 | 级别 |
|---|---|---|---|---|
| NT-23 | 缩略图缺失 (非阻断) | `thumbnail_path` 指向不存在文件 | `WARN thumbnail missing, continuing` | P2 |
| NT-24 | receipt 目录不可写 | `receipt_output_dir` 无权限 | `FAIL receipt dir unwritable`；同时写 emergency journal | P1 |
| NT-25 | 本地日配额超限 | 单日 upload 计数 > `daily_upload_limit` | `FAIL local daily upload quota exhausted` | P1 |

## Phase 5: Private upload smoke test

| # | Guard | 测试输入 | 预期 | 级别 |
|---|---|---|---|---|
| NT-26 | 完整 private upload | 合法 Contract + 有效 token + test channel | 上传成功，receipt 含 video_id | — |
| NT-27 | 上传后删除 | 确认 YouTube Studio 可见后删除 | video 被删除, receipt 保留审计记录 | — |

## 测试环境

| 要求 | 说明 |
|---|---|
| 测试 token | disposable token，youtube.upload scope only |
| 测试频道 | 专用 test channel（不承载生产视频） |
| 测试视频 | ≤30s test clip（非 N001 成品）；private 上传后删除 |
| secret manifest | `{ "secrets": { "youtube_oauth_test": "/path/to/token.json" } }` |
| local_quota | Project 侧设置 `daily_upload_limit: 1` 供 NT-25 |

## 验收标准

- 19 项 P0 全部 PASS
- 5 项 P1 全部 PASS 或记录为已知限制
- 1 项 P2 PASS
- Smoke test 产生 `video_id`，YouTube Studio 可确认
- 所有 Schema 验证由 `jsonschema.Draft202012Validator` 执行
- `guarded_upload_task.schema.json` 纳入 `protocol_lock.json`
