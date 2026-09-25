"""Independent gRPC status/metadata reference for grpcfaultd verifier."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

APP = Path("/app")
FRAMEPROBE = "/usr/local/bin/frameprobe"
GRPCURL = "/usr/local/bin/grpcurl"
ADDR = "127.0.0.1:50051"

TRAILER_KEYS = ("x-trace-tail", "x-audit-tail", "x-tenant-tail")
DETAIL_KEYS = ("fault-domain", "fault-reason", "fault-scope")


@dataclass
class Catalog:
    seed: str
    trailer_key: str
    detail_key: str


def fnv1a64(seed: str) -> int:
    h = 0xCBF29CE484222325
    for b in seed.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def configure_catalog(seed: str) -> Catalog:
    n = fnv1a64(seed)
    return Catalog(
        seed=seed,
        trailer_key=TRAILER_KEYS[n % len(TRAILER_KEYS)],
        detail_key=DETAIL_KEYS[(n >> 8) % len(DETAIL_KEYS)],
    )


def run_frameprobe(
    seed: str,
    case_id: str,
    mode: str = "unary",
    payload_size: int = 0,
) -> dict:
    cmd = [
        FRAMEPROBE,
        "--addr",
        ADDR,
        "--seed",
        seed,
        "--case",
        case_id,
        "--mode",
        mode,
        "--payload-size",
        str(payload_size),
    ]
    proc = subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def expected_probe(seed: str, case_id: str, mode: str = "unary", payload_size: int = 0) -> dict:
    catalog = configure_catalog(seed)
    if case_id == "trailer-split":
        return {
            "code": "OK",
            "message": "",
            "headers": {},
            "trailers": {catalog.trailer_key: "tail-only" if mode == "unary" else "stream-tail"},
            "detail_reason": "",
        }
    if case_id == "status-details":
        return {
            "code": "FailedPrecondition",
            "message": "precondition failed",
            "headers": {},
            "trailers": {},
            "detail_reason": catalog.detail_key,
        }
    if case_id == "ctx-cancel":
        return {
            "code": "Canceled",
            "message": "context canceled",
            "headers": {},
            "trailers": {},
            "detail_reason": "",
        }
    if case_id == "recv-limit-body":
        if payload_size > 48:
            return {
                "code": "ResourceExhausted",
                "message": "recv limit exceeded",
                "headers": {},
                "trailers": {},
                "detail_reason": "",
            }
        return {
            "code": "OK",
            "message": "",
            "headers": {},
            "trailers": {},
            "detail_reason": "",
        }
    if case_id in {"unary-shape", "stream-shape"}:
        return {
            "code": "InvalidArgument",
            "message": f"{'unary' if case_id == 'unary-shape' else 'stream'} invalid argument",
            "headers": {},
            "trailers": {},
            "detail_reason": "",
        }
    raise ValueError(f"unknown case {case_id}")


def grpcurl_admin(seed: str) -> dict:
    proc = subprocess.run(
        [
            GRPCURL,
            "-plaintext",
            "-d",
            json.dumps({"seed": seed}),
            ADDR,
            "fault.v1.Admin/ConfigureCatalog",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def sha256_file(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()
