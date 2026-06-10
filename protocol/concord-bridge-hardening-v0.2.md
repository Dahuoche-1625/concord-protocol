# Concord Bridge Hardening v0.2

> Status: pilot-validated draft
> Scope: file-driven and distributed Bridge Object implementations
> Relationship: extends the Domain Separation Model without claiming OS-level enforcement

## 1. Purpose

This document turns Bridge Loop pilot findings into protocol-level constraints. It defines how projects and Runtime Mesh implementations exchange minimum context, claim work, prove outputs, and close leases without weakening domain separation.

The standard loop is:

```text
TaskContract
  -> TaskDispatch
  -> TaskLease(pending)
  -> claim(active)
  -> execute
  -> ExecutionReceipt(done|partial_done|failed|invalid)
  -> guarded_verify(pass|fail)
  -> release(released)
  -> ReviewResult
```

## 2. Lifecycle Rules

- A worker MUST claim only a `pending` lease.
- A distributed TaskContract MUST NOT bind a concrete worker before lease claim.
- A worker MUST stop when its lease expires unless renewal was confirmed before `lease_until`.
- A receipt written by an expired or mismatched lease MUST be rejected.
- `guarded_verify` MUST complete before a successful lease release.
- The executing worker MUST NOT author the final ReviewResult for its own critical output.
- `partial_done -> dispatched` MUST state whether prior artifacts are inherited or discarded. Inherited artifacts MUST be referenced through `source_refs` and the TaskContract retry policy.

## 3. Indirect Deployment References

Machine-specific paths and credentials MUST remain in local deployment configuration. Contracts and boundaries SHOULD reference them indirectly, for example:

```text
manifest://output.final_dir
manifest://input.raw_source_dir
secret-ref://provider/account-a
```

An adapter that resolves indirect references MUST:

1. resolve nested keys deterministically;
2. reject missing values and placeholder values;
3. normalize the real path before scope comparison;
4. evaluate symbolic links against their final target;
5. avoid writing resolved secrets into Bridge Objects or audit events.

The URI scheme is adapter-defined. The security properties above are mandatory.

## 4. External Artifacts

Large or mutable artifacts SHOULD live outside protocol and project source repositories. ExecutionReceipt references MUST include enough evidence to verify the artifact without embedding it:

```json
{
  "artifact_id": "artifact-001",
  "uri": "external://deployment/output/result.bin",
  "sha256": "HEX_SHA256",
  "size_bytes": 1,
  "created_at": "2026-01-01T00:00:00Z"
}
```

Repositories MAY retain contracts, receipts, audit records, schemas, and templates. They MUST NOT treat large runtime output as protocol source.

## 5. Secret Stripping

Before writing an ExecutionReceipt, ReviewResult, audit event, or result object, implementations MUST recursively remove secret-bearing fields.

Default sensitive key fragments include:

```text
token
secret
credential
oauth
api_key
bearer
password
cookie
```

Secret stripping failure is a blocking failure. Implementations MUST NOT fall back to writing the unfiltered object.

## 6. Guarded Verify

`guarded_verify` means pre-execution validation plus post-execution verification. It is stronger than `verify_only`, but it is not a sandbox.

A conforming guard MUST check at least:

- identity, capability, protocol compatibility, and active lease before execution;
- artifact existence and normalized scope;
- non-empty artifact hash and positive size;
- receipt-to-lease and receipt-to-task binding;
- blocking violations before accepting a result;
- audit coverage for claim, execution result, guard judgment, and release.

When a blocking violation exists, the receipt status MUST be `invalid`. Safe cleanup of newly created out-of-scope files is allowed. Rollback of modified files requires a pre-task snapshot.

## 7. Runtime Admission

A Runtime node MUST pass its declared deployment profile before claiming work. The profile SHOULD verify required executables, writable scopes, contract versions, local configuration completeness, and required accelerators.

Missing tools, unresolved placeholders, incompatible protocol versions, or failed capability probes MUST prevent lease claim. Business-specific probes belong to the Application or Runtime profile, not this protocol.

## 8. Privileged Side Effects

Public publishing, financial actions, destructive operations, credential rotation, and other privileged side effects require explicit Project Domain authorization.

Runtime MUST NOT infer authorization from tool availability. The TaskContract must identify the authorization reference, expected target, acceptance criteria, and review policy. Dry-run or private-mode validation SHOULD precede irreversible execution.

## 9. Protocol Lock

Runtime releases SHOULD carry a machine-readable `protocol_lock.json` containing:

- the Concord version and source commit;
- hashes of distributed schemas;
- the guard profile hash;
- supported compatibility range;
- release/example status.

An example lock or a lock with a mismatched hash MUST NOT authorize production execution. The normative shape is `schemas/protocol_lock.schema.json`.

## 10. Conformance Boundary

Concord defines object semantics and verification requirements. It does not define the queue, transport, business workflow, media pipeline, cloud provider, or operating system. Those belong to Runtime and Application implementations.
