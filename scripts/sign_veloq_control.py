#!/usr/bin/env python3
"""Validate and sign the VeloQ control payload."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives import serialization


ROOT = Path(__file__).resolve().parents[1]
CONTROL_FILE = ROOT / "veloq" / "control.json"
MANIFEST_FILE = ROOT / "veloq" / "manifest.json"
KEY_ID = "veloq-ed25519-2026-01"
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
MODEL_NAME = re.compile(r"^[A-Za-z0-9._:-]+/[A-Za-z0-9._:+-]+$")


def canonical_json(payload: dict) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def validate_utc(value: str) -> None:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")


def load_and_validate() -> dict:
    payload = json.loads(CONTROL_FILE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("control payload must be an object")
    if payload.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(payload.get("revision"), int) or payload["revision"] < 1:
        raise ValueError("revision must be a positive integer")
    if payload.get("enabled") not in (True, False):
        raise ValueError("enabled must be true or false")
    if not MODEL_NAME.fullmatch(str(payload.get("model", "")).strip()):
        raise ValueError("model must look like provider/model-name")

    grace = payload.get("offline_grace_hours")
    if not isinstance(grace, int) or not 0 <= grace <= 72:
        raise ValueError("offline_grace_hours must be between 0 and 72")
    validate_utc(str(payload.get("updated_at", "")))

    licenses = payload.get("licenses")
    if not isinstance(licenses, list):
        raise ValueError("licenses must be an array")

    seen = set()
    for item in licenses:
        if not isinstance(item, dict):
            raise ValueError("each license must be an object")
        license_hash = str(item.get("license_sha256", "")).lower()
        if not HEX_64.fullmatch(license_hash):
            raise ValueError("license_sha256 must be 64 lowercase hex characters")
        if license_hash in seen:
            raise ValueError("duplicate license hash")
        seen.add(license_hash)

        device_hash = str(item.get("device_sha256") or "").lower()
        if device_hash and not HEX_64.fullmatch(device_hash):
            raise ValueError("device_sha256 must be null or 64 lowercase hex characters")
        if item.get("status") not in ("active", "revoked"):
            raise ValueError("license status must be active or revoked")
        if item.get("expires_at"):
            validate_utc(str(item["expires_at"]))

        item["license_sha256"] = license_hash
        item["device_sha256"] = device_hash or None
        item["label"] = str(item.get("label", "Customer")).strip()[:80] or "Customer"
        item["plan_name"] = (
            str(item.get("plan_name", "VeloQ License")).strip()[:80] or "VeloQ License"
        )

    payload["licenses"] = sorted(
        licenses,
        key=lambda item: (item["label"].lower(), item["license_sha256"]),
    )
    return payload


def main() -> None:
    private_pem = os.environ.get("VELOQ_SIGNING_KEY_PEM", "").strip()
    if not private_pem:
        raise RuntimeError("VELOQ_SIGNING_KEY_PEM repository secret is missing")

    payload = load_and_validate()
    canonical = canonical_json(payload)
    private_key = serialization.load_pem_private_key(
        private_pem.encode("ascii"),
        password=None,
    )
    signature = private_key.sign(canonical)
    envelope = {
        "algorithm": "Ed25519",
        "key_id": KEY_ID,
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "signature": base64.b64encode(signature).decode("ascii"),
    }
    MANIFEST_FILE.write_text(
        json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Signed VeloQ control revision {payload['revision']} "
        f"with {len(payload['licenses'])} license(s)."
    )


if __name__ == "__main__":
    main()
