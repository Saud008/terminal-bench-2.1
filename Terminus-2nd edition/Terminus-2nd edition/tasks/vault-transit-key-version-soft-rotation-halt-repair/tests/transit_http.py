"""HTTP helpers for transit-mock verifier tests."""

from __future__ import annotations

import base64
import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class CurlResponse:
    status: int
    headers: dict[str, str]
    body: str
    json_data: Any | None


def curl_request(method: str, url: str, payload: dict | None = None) -> CurlResponse:
    cmd = ["curl", "-sS", "-i", "-X", method, url]
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(payload)])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    raw = proc.stdout
    header_blob, _, body = raw.partition("\r\n\r\n")
    if not body and "\n\n" in raw:
        header_blob, _, body = raw.partition("\n\n")
    lines = header_blob.splitlines()
    status = 0
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        headers[key.strip().lower()] = val.strip()
        if key.strip().lower() == "status":
            continue
    if lines:
        parts = lines[0].split()
        if len(parts) >= 2:
            status = int(parts[1])
    json_data = None
    if body.strip():
        try:
            json_data = json.loads(body)
        except json.JSONDecodeError:
            json_data = None
    return CurlResponse(status=status, headers=headers, body=body, json_data=json_data)


def b64_text(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def load_policy(base: str, key: str, policy_file: str) -> CurlResponse:
    return curl_request(
        "POST",
        f"{base}/v1/transit/keys/{key}/config",
        {"policy_file": policy_file},
    )


def get_policy(base: str, key: str) -> CurlResponse:
    return curl_request("GET", f"{base}/v1/transit/keys/{key}/policy")


def rotate(base: str, key: str) -> CurlResponse:
    return curl_request("POST", f"{base}/v1/transit/keys/{key}/rotate")


def encrypt(base: str, key: str, plaintext: str, context: str = "", key_version: int = 0) -> CurlResponse:
    return curl_request(
        "POST",
        f"{base}/v1/transit/keys/{key}/encrypt",
        {
            "plaintext": b64_text(plaintext),
            "context": context,
            "key_version": key_version,
        },
    )


def decrypt(base: str, key: str, ciphertext: str) -> CurlResponse:
    return curl_request(
        "POST",
        f"{base}/v1/transit/keys/{key}/decrypt",
        {"ciphertext": ciphertext},
    )


def batch_encrypt(base: str, key: str, items: list[tuple[str, str]]) -> CurlResponse:
    batch_input = [
        {"plaintext": b64_text(text), "context": ctx}
        for text, ctx in items
    ]
    return curl_request(
        "POST",
        f"{base}/v1/transit/keys/{key}/encrypt/batch",
        {"batch_input": batch_input},
    )


def delete_version(base: str, key: str, version: int) -> CurlResponse:
    return curl_request("DELETE", f"{base}/v1/transit/keys/{key}/versions/{version}")


def set_halt(base: str, key: str, after: int) -> CurlResponse:
    return curl_request(
        "POST",
        f"{base}/v1/transit/keys/{key}/halt",
        {"soft_rotation_halt_after_version": after},
    )
