# Changelog

All notable protocol changes are recorded here. Concord is still alpha; schema compatibility is documented per release rather than implied.

## v0.2.0-alpha - 2026-06-15

### Added

- Project Domain / Runtime Mesh separation with persistent Bridge Objects.
- Task model split: TaskContract, TaskDispatch, TaskLease, ExecutionReceipt, and ReviewResult.
- `guarded_verify`, external artifact references, secret stripping, and protocol-lock schemas.
- Guarded Upload TaskContract v0.2 and ApprovalGrant v0.1.
- Artifact, channel, privacy-ceiling, expiration, HMAC, revocation, and idempotency checks.
- Executable schema and cross-field validation with positive and negative tests.
- Pilot plans, acceptance criteria, and a production reference implementation boundary.

### Security boundary

- This release does not provide OS-level sandboxing.
- `guarded_verify` rejects invalid results and requires evidence; host-level prevention remains an implementation responsibility.

### Compatibility

- Existing v0.1 identity, capability, boundary, and audit objects remain valid foundations.
- v0.2 task and upload objects require new schemas and explicit protocol-version negotiation.

## v0.1-alpha - 2026-05-28

- Initial security kernel, capability records, agent boundaries, RuntimeGuard, AuditLog, and domain-separation draft.
