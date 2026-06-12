#!/usr/bin/env python3
"""Cross-field validator for guarded upload TaskContracts.

JSON Schema (Draft202012) checks structural validity. This validator
enforces semantic constraints that span multiple fields:

  - approval_grant.artifact_sha256 == upload_parameters.artifact_ref.sha256
  - approval_grant.channel_id == channel_binding.expected_channel_id
  - metadata.privacy_status <= approval_grant.max_privacy (层级)
  - approval_grant.revoked == false
  - approval_grant.expires_at is in the future
  - approval_grant.signed_fields covers all required fields

Usage:
  python3 validate_guarded_upload_contract.py contract.json
  python3 validate_guarded_upload_contract.py contract.json --skip-expiry
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

PRIVACY_HIERARCHY = {"private": 1, "unlisted": 2, "public": 3}
REQUIRED_SIGNED_FIELDS = frozenset([
    "approval_id", "action", "artifact_sha256", "channel_id",
    "max_privacy", "expires_at", "revoked",
])
URI_FIELDS = (
    ("input_refs",),
    ("upload_parameters", "artifact_ref", "path"),
    ("upload_parameters", "metadata", "thumbnail_path"),
    ("upload_parameters", "receipt_config", "receipt_output_dir"),
    ("upload_parameters", "receipt_config", "emergency_journal_dir"),
    ("revocation_check", "revocation_list_ref"),
)


class ContractValidationError(ValueError):
    pass


def load(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractValidationError(f"root must be an object: {path}")
    return data


def ensure(value: Any, message: str) -> None:
    if not value:
        raise ContractValidationError(message)


def parse_datetime(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractValidationError(f"invalid {field}: {value}") from exc
    ensure(parsed.tzinfo is not None, f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate_scoped_uri(value: str, field: str) -> None:
    parsed = urlsplit(value)
    ensure(parsed.scheme in {"manifest", "external"}, f"{field} uses unsupported scheme")
    ensure(bool(parsed.netloc or parsed.path.strip("/")), f"{field} must identify a resource")
    segments = [segment for segment in parsed.path.split("/") if segment]
    ensure(".." not in segments and "." not in segments, f"{field} contains path traversal")
    ensure(not parsed.query and not parsed.fragment, f"{field} must not contain query or fragment")


def nested_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate(contract: dict[str, Any], skip_expiry: bool = False) -> list[str]:
    passed: list[str] = []

    grant = contract.get("approval_grant")
    ensure(isinstance(grant, dict), "approval_grant must be an object")
    upload = contract.get("upload_parameters")
    ensure(isinstance(upload, dict), "upload_parameters must be an object")
    artifact = upload.get("artifact_ref")
    ensure(isinstance(artifact, dict), "upload_parameters.artifact_ref must be an object")
    metadata = upload.get("metadata")
    ensure(isinstance(metadata, dict), "upload_parameters.metadata must be an object")
    binding = upload.get("channel_binding")
    ensure(isinstance(binding, dict), "upload_parameters.channel_binding must be an object")
    gates = contract.get("validation_gates")
    ensure(isinstance(gates, dict), "validation_gates must be an object")

    # (1) artifact SHA256 match
    approval_sha = grant.get("artifact_sha256")
    contract_sha = artifact.get("sha256")
    ensure(approval_sha and contract_sha,
           "artifact_sha256 must be present in both approval_grant and artifact_ref")
    ensure(approval_sha == contract_sha,
           f"artifact SHA256 mismatch: approval={approval_sha} != contract={contract_sha}")
    passed.append("artifact_sha256_match")

    # (2) channel_id match
    approval_channel = grant.get("channel_id")
    binding_channel = binding.get("expected_channel_id")
    ensure(approval_channel and binding_channel,
           "channel_id must be present in both approval_grant and channel_binding")
    ensure(approval_channel == binding_channel,
           f"channel_id mismatch: approval={approval_channel} != binding={binding_channel}")
    passed.append("channel_id_match")

    # (3) privacy hierarchy
    max_priv = grant.get("max_privacy", "private")
    req_priv = metadata.get("privacy_status", "private")
    ensure(max_priv in PRIVACY_HIERARCHY, f"invalid max_privacy: {max_priv}")
    ensure(req_priv in PRIVACY_HIERARCHY, f"invalid privacy_status: {req_priv}")
    ensure(PRIVACY_HIERARCHY[req_priv] <= PRIVACY_HIERARCHY[max_priv],
           f"privacy exceeds approval: requested {req_priv} > max {max_priv}")
    passed.append("privacy_hierarchy_ok")

    # (4) not revoked
    ensure(not bool(grant.get("revoked", False)),
           "approval_grant has been revoked")
    passed.append("not_revoked")

    # (5) expiry
    expires_str = grant.get("expires_at", "")
    if expires_str and not skip_expiry:
        expires = parse_datetime(expires_str, "approval_grant.expires_at")
        now = datetime.now(timezone.utc)
        ensure(expires > now,
               f"approval expired at {expires_str} (now: {now.isoformat()})")
    passed.append("expiry_ok" if not skip_expiry else "expiry_skipped")

    context_expires = contract.get("context_expires_at", "")
    if context_expires and not skip_expiry:
        context_deadline = parse_datetime(context_expires, "context_expires_at")
        ensure(context_deadline > datetime.now(timezone.utc),
               f"contract context expired at {context_expires}")
    passed.append("context_expiry_ok" if not skip_expiry else "context_expiry_skipped")

    # (6) signed fields completeness
    proof = grant.get("source_proof", {})
    signed = set(proof.get("signed_fields", []))
    missing = REQUIRED_SIGNED_FIELDS - signed
    ensure(not missing,
           f"approval_grant.source_proof.signed_fields missing: {sorted(missing)}")
    passed.append("signed_fields_complete")

    # (7) idempotency key present
    ensure(bool(contract.get("idempotency_key")), "idempotency_key is required")
    passed.append("idempotency_key_present")

    # (8) receipt_config present with emergency journal
    receipt = upload.get("receipt_config", {})
    ensure(bool(receipt.get("emergency_journal_dir")),
           "receipt_config.emergency_journal_dir is required")
    passed.append("emergency_journal_configured")

    # (9) revocation check configured
    rev_check = contract.get("revocation_check")
    ensure(isinstance(rev_check, dict) and rev_check.get("revocation_list_ref"),
           "revocation_check with revocation_list_ref is required")
    passed.append("revocation_check_configured")

    for path in URI_FIELDS:
        value = nested_value(contract, path)
        if value is None:
            continue
        field = ".".join(path)
        if isinstance(value, list):
            for index, item in enumerate(value):
                validate_scoped_uri(item, f"{field}[{index}]")
        else:
            validate_scoped_uri(value, field)
    passed.append("scoped_uris_valid")

    return passed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-field validator for guarded upload TaskContracts"
    )
    parser.add_argument("contract", help="Path to TaskContract JSON")
    parser.add_argument("--skip-expiry", action="store_true",
                        help="Skip expiry check (for test environments)")
    args = parser.parse_args()

    try:
        contract = load(args.contract)

        # structural schema validation
        try:
            from jsonschema import Draft202012Validator, FormatChecker, ValidationError
            from referencing import Registry, Resource
        except ImportError as exc:
            print(
                "DEPENDENCY_MISSING: install jsonschema>=4,<5 before validation",
                file=sys.stderr,
            )
            return 3
        schema_dir = Path(__file__).resolve().parent.parent / "schemas"
        upload_schema = json.loads(
            (schema_dir / "guarded_upload_task.schema.json").read_text(encoding="utf-8")
        )
        grant_schema = json.loads(
            (schema_dir / "approval_grant.schema.json").read_text(encoding="utf-8")
        )
        registry = Registry().with_resource(
            grant_schema["$id"], Resource.from_contents(grant_schema)
        )
        Draft202012Validator(
            upload_schema,
            registry=registry,
            format_checker=FormatChecker(),
        ).validate(contract)

        results = validate(contract, skip_expiry=args.skip_expiry)
        print(f"VALID: {len(results)} checks passed")
        for r in results:
            print(f"  + {r}")
        return 0
    except ContractValidationError as exc:
        print(f"CONTRACT_INVALID: {exc}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        location = ".".join(str(i) for i in exc.absolute_path) or "root"
        print(f"SCHEMA_INVALID at {location}: {exc.message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
