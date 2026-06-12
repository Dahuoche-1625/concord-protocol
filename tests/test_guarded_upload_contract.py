from __future__ import annotations

import copy
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "tools/validate_guarded_upload_contract.py"
    spec = importlib.util.spec_from_file_location("guarded_upload_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator_module = load_module()


def future(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def valid_contract() -> dict:
    digest = "a" * 64
    channel_id = "UCAbCdEfGhIjKlMnOpQrStUv"
    return {
        "task_id": "TASK-UPLOAD-1",
        "task_mode": "guarded_upload",
        "project_id": "PROJECT-1",
        "application_id": "APP-1",
        "required_protocol_version": "0.2",
        "required_capabilities": ["youtube_api_upload_capable"],
        "context_scope": "upload_only",
        "context_expires_at": future(2),
        "input_refs": ["external://deployment/output/video.mp4"],
        "redactions": ["oauth_token"],
        "risk_level": "high",
        "acceptance_criteria": ["private upload receipt validates"],
        "contract_clarity_score": 5,
        "source_proof": {
            "method": "hash_chain",
            "signed_fields": ["task_id"],
            "value": "contract-proof",
        },
        "idempotency_key": "upload-key-0001",
        "execution_host": "task_scheduler",
        "upload_parameters": {
            "artifact_ref": {
                "path": "external://deployment/output/video.mp4",
                "sha256": digest,
                "size_bytes": 10_485_760,
                "duration_seconds": 60,
            },
            "metadata": {
                "title": "Guarded upload smoke test",
                "description": "Private disposable smoke-test video.",
                "privacy_status": "private",
            },
            "channel_binding": {
                "channel_key": "test-channel",
                "expected_channel_id": channel_id,
                "token_ref": "secret://youtube_oauth_test",
            },
            "receipt_config": {
                "receipt_output_dir": "manifest://receipts/upload",
                "emergency_journal_dir": "manifest://journals/upload",
            },
        },
        "validation_gates": {
            "require_owner_approval": True,
            "require_expected_channel_id_match": True,
            "require_token_existence": True,
            "require_receipt_on_completion": True,
            "require_metadata_completeness": True,
            "block_public_without_explicit_approval": True,
            "block_unknown_channel": True,
            "max_retries": 3,
            "local_quota_gate_enabled": True,
            "daily_upload_limit": 1,
        },
        "approval_grant": {
            "approval_id": "12345678-1234-1234-1234-123456789abc",
            "action": "upload",
            "artifact_sha256": digest,
            "channel_id": channel_id,
            "max_privacy": "private",
            "granted_by": "owner",
            "granted_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": future(1),
            "revoked": False,
            "source_proof": {
                "method": "hmac",
                "key_ref": "secret://owner_approval_hmac",
                "signed_fields": [
                    "approval_id",
                    "action",
                    "artifact_sha256",
                    "channel_id",
                    "max_privacy",
                    "expires_at",
                    "revoked",
                ],
                "value": "signed-proof-value",
            },
        },
        "revocation_check": {
            "revocation_list_ref": "manifest://approvals/revocations.json",
            "max_staleness_seconds": 60,
        },
    }


def sign_contract(contract: dict, key: bytes) -> None:
    grant = contract["approval_grant"]
    fields = grant["source_proof"]["signed_fields"]
    payload = "|".join(
        f"{field}={json.dumps(grant.get(field), sort_keys=True)}" for field in fields
    )
    grant["source_proof"]["value"] = hmac.new(
        key, payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


class GuardedUploadContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema_dir = ROOT / "schemas"
        cls.schema = json.loads(
            (schema_dir / "guarded_upload_task.schema.json").read_text(encoding="utf-8")
        )
        grant_schema = json.loads(
            (schema_dir / "approval_grant.schema.json").read_text(encoding="utf-8")
        )
        registry = Registry().with_resource(
            grant_schema["$id"], Resource.from_contents(grant_schema)
        )
        cls.structural = Draft202012Validator(
            cls.schema,
            registry=registry,
            format_checker=FormatChecker(),
        )

    def test_valid_contract_passes_structure_and_semantics(self) -> None:
        contract = valid_contract()
        self.structural.validate(contract)
        checks = validator_module.validate(contract)
        self.assertIn("artifact_sha256_match", checks)
        self.assertIn("scoped_uris_valid", checks)

    def test_receipt_config_must_be_nested_under_upload_parameters(self) -> None:
        contract = valid_contract()
        receipt = contract["upload_parameters"].pop("receipt_config")
        contract["receipt_config"] = receipt
        with self.assertRaises(ValidationError):
            self.structural.validate(contract)

    def test_cross_field_mismatches_are_rejected(self) -> None:
        cases = []

        artifact = valid_contract()
        artifact["approval_grant"]["artifact_sha256"] = "b" * 64
        cases.append(artifact)

        channel = valid_contract()
        channel["approval_grant"]["channel_id"] = "UCXyZxYzXyZxYzXyZxYzXyZxY"
        cases.append(channel)

        privacy = valid_contract()
        privacy["upload_parameters"]["metadata"]["privacy_status"] = "public"
        cases.append(privacy)

        revoked = valid_contract()
        revoked["approval_grant"]["revoked"] = True
        cases.append(revoked)

        for contract in cases:
            with self.subTest(contract=contract):
                with self.assertRaises(validator_module.ContractValidationError):
                    validator_module.validate(contract)

    def test_expired_contract_and_approval_are_rejected(self) -> None:
        approval = valid_contract()
        approval["approval_grant"]["expires_at"] = "2020-01-01T00:00:00Z"
        with self.assertRaises(validator_module.ContractValidationError):
            validator_module.validate(approval)

        context = valid_contract()
        context["context_expires_at"] = "2020-01-01T00:00:00Z"
        with self.assertRaises(validator_module.ContractValidationError):
            validator_module.validate(context)

    def test_signed_fields_cannot_be_reduced(self) -> None:
        contract = valid_contract()
        contract["approval_grant"]["source_proof"]["signed_fields"] = ["approval_id"]
        with self.assertRaises(ValidationError):
            self.structural.validate(contract)

    def test_path_traversal_is_rejected(self) -> None:
        contract = valid_contract()
        contract["upload_parameters"]["artifact_ref"]["path"] = (
            "manifest://output/../../secrets/token.json"
        )
        self.structural.validate(contract)
        with self.assertRaises(validator_module.ContractValidationError):
            validator_module.validate(contract)

    def test_revocation_check_is_required(self) -> None:
        contract = valid_contract()
        del contract["revocation_check"]
        with self.assertRaises(ValidationError):
            self.structural.validate(contract)

    def test_cli_is_fail_closed_without_runtime_proofs(self) -> None:
        contract = valid_contract()
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/validate_guarded_upload_contract.py"), str(contract_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--signing-key is required", result.stderr)

    def test_cli_accepts_hmac_and_fresh_revocation_list(self) -> None:
        key = b"test-owner-key"
        contract = valid_contract()
        sign_contract(contract, key)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract_path = root / "contract.json"
            revocation_path = root / "revocations.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            revocation_path.write_text(
                json.dumps({"revoked_approval_ids": []}), encoding="utf-8"
            )
            env = dict(os.environ)
            env["CONCORD_SIGNING_KEY_OWNER_APPROVAL_HMAC"] = key.decode()
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/validate_guarded_upload_contract.py"),
                    str(contract_path),
                    "--signing-key",
                    "secret://owner_approval_hmac",
                    "--revocation-list",
                    str(revocation_path),
                ],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("hmac_signature_verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
