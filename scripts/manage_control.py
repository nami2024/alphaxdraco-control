#!/usr/bin/env python3
"""Update and sign the AlphaXDraco control manifest."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


ROOT = Path(__file__).resolve().parents[1]
CONTROL_FILE = ROOT / "control.json"
MANIFEST_FILE = ROOT / "manifest.json"
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
MODEL_NAME = re.compile(r"^[A-Za-z0-9._:-]+/[A-Za-z0-9._:-]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_optional_hash(value: str) -> str | None:
    value = value.strip().lower()
    if not value:
        return None
    if not HEX_64.fullmatch(value):
        raise ValueError("device_hash must be exactly 64 hexadecimal characters")
    return value


def normalize_expiry(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        value += "T23:59:59Z"
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(payload: dict) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def load_control() -> dict:
    with CONTROL_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("licenses"), list):
        raise ValueError("control.json has an invalid structure")
    return data


def save_signed(control: dict) -> None:
    private_pem = os.environ.get("LICENSE_SIGNING_KEY_PEM", "").strip()
    if not private_pem:
        raise RuntimeError("LICENSE_SIGNING_KEY_PEM secret is missing")

    control["updated_at"] = utc_now()
    control["licenses"] = sorted(
        control["licenses"],
        key=lambda item: (str(item.get("label", "")).lower(), str(item.get("license_sha256", ""))),
    )
    canonical = canonical_json(control)
    private_key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    signature = private_key.sign(canonical, padding.PKCS1v15(), hashes.SHA256())

    CONTROL_FILE.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MANIFEST_FILE.write_text(
        json.dumps(
            {
                "algorithm": "RSASSA-PKCS1-v1_5-SHA256",
                "payload": control,
                "signature": base64.b64encode(signature).decode("ascii"),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def find_license(control: dict, license_hash: str) -> dict | None:
    return next(
        (item for item in control["licenses"] if item.get("license_sha256") == license_hash),
        None,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("add", "revoke", "activate", "model", "resign"))
    parser.add_argument("--license-hash", default="")
    parser.add_argument("--device-hash", default="")
    parser.add_argument("--expires-at", default="")
    parser.add_argument("--label", default="")
    parser.add_argument("--model", default="")
    args = parser.parse_args()

    control = load_control()
    license_hash = args.license_hash.strip().lower()

    if args.action in {"add", "revoke", "activate"}:
        if not HEX_64.fullmatch(license_hash):
            raise ValueError("license_hash must be exactly 64 hexadecimal characters")

    if args.action == "add":
        record = find_license(control, license_hash)
        values = {
            "license_sha256": license_hash,
            "device_sha256": normalize_optional_hash(args.device_hash),
            "status": "active",
            "expires_at": normalize_expiry(args.expires_at),
            "label": args.label.strip()[:80] or "Customer",
        }
        if record is None:
            control["licenses"].append(values)
        else:
            record.update(values)
    elif args.action in {"revoke", "activate"}:
        record = find_license(control, license_hash)
        if record is None:
            raise ValueError("license hash was not found")
        record["status"] = "revoked" if args.action == "revoke" else "active"
    elif args.action == "model":
        model = args.model.strip()
        if not MODEL_NAME.fullmatch(model):
            raise ValueError("model must look like provider/model-name")
        control["model"] = model

    save_signed(control)
    print(f"Control manifest updated: action={args.action}")


if __name__ == "__main__":
    main()
