"""Shared livattest HTTP harness for verifier modules."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

APP = Path("/app")
CONFIG = APP / "config" / "livattest.json"
REPORT = APP / "output" / "attest-report.json"
SNAPSHOT = APP / "state" / "witness-snapshot.json"
DB = APP / "work" / "livattest.db"
CLI = Path("/usr/local/bin/livattest")
SEED = os.environ.get("VERIFIER_SEED", "livattest-seed-11")
EXTRA_SEEDS = ("livattest-matrix-3", "livattest-matrix-19", "livattest-matrix-47")
SLICES = Path(__file__).resolve().parent / "oracle_slices"

SLICE_TARGETS = {
    "continuity": APP / "internal/policy/continuity_gate.go",
    "trust": APP / "internal/vault/trust_bind.go",
    "ban": APP / "internal/seal/ban_revoke.go",
    "chain": APP / "internal/witness/chain_write.go",
    "emit": APP / "internal/export/digest_emit.go",
    "pin": APP / "internal/clock/pin_clock.go",
}
SLICE_MODULES = tuple(SLICE_TARGETS.keys())

PROTECTED_SHA256: dict[str, str] = {}


def load_protected(digest_map: dict[str, str]) -> None:
    global PROTECTED_SHA256
    PROTECTED_SHA256 = dict(digest_map)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stop_daemon() -> None:
    subprocess.run(["pkill", "-9", "-x", "livattest"], check=False)
    time.sleep(0.3)


def start_daemon() -> None:
    stop_daemon()
    subprocess.Popen(
        [str(CLI), "serve", "--config", str(CONFIG)],
        cwd=APP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=0.5)
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("livattest did not start")


def http_json(method: str, path: str, body: dict | None = None, mono_ms: int | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if mono_ms is not None:
        headers["X-Test-Mono-Ms"] = str(mono_ms)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:8080{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if not raw:
            return exc.code, {}
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def reset_state() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def rebuild_binary() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd=APP,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def trust_bind(token: str, session_id: str, client_ms: int, mono_ms: int = 0) -> str:
    status, body = http_json(
        "POST",
        "/v1/trust/bind",
        {"token": token, "session_id": session_id, "client_ms": client_ms},
        mono_ms=mono_ms,
    )
    assert status == 200, body
    return body["admission_ticket"]


def attest_batch(
    token: str,
    session_id: str,
    ticket: str,
    beats: list[dict],
    mono_ms: int,
    *,
    expect_ok: bool = True,
) -> int:
    status, body = http_json(
        "POST",
        "/v1/attest/batch",
        {
            "token": token,
            "session_id": session_id,
            "admission_ticket": ticket,
            "beats": beats,
        },
        mono_ms=mono_ms,
    )
    if expect_ok:
        assert status == 200, body
    return status


def attest_export(token: str, session_id: str, mono_ms: int = 0) -> dict:
    status, body = http_json(
        "POST",
        "/v1/attest/export",
        {"token": token, "session_id": session_id},
        mono_ms=mono_ms,
    )
    assert status == 200, body
    assert REPORT.is_file()
    return json.loads(REPORT.read_text(encoding="utf-8"))


def run_discontinuity_batches(ref) -> str:
    ticket = trust_bind(ref.token, ref.session_id, ref.anchor_client, mono_ms=0)
    base = ref.anchor_client
    attest_batch(ref.token, ref.session_id, ticket, [{"seq": 1, "client_ms": base}], 500)
    attest_batch(
        ref.token,
        ref.session_id,
        ticket,
        [{"seq": 4, "client_ms": base + 1200}],
        1500,
    )
    attest_batch(
        ref.token,
        ref.session_id,
        ticket,
        [{"seq": 2, "client_ms": base + 400}],
        2000,
    )
    attest_batch(
        ref.token,
        ref.session_id,
        ticket,
        [{"seq": 3, "client_ms": base + 800}],
        2500,
    )
    return ticket


def restore_ship_slices() -> None:
    for name, target in SLICE_TARGETS.items():
        shutil.copy(SLICES / f"ship_{name}.go", target)


@contextmanager
def oracle_slices(*names: str):
    originals = {mod: SLICE_TARGETS[mod].read_text(encoding="utf-8") for mod in SLICE_MODULES}
    try:
        restore_ship_slices()
        for name in names:
            shutil.copy(SLICES / f"oracle_{name}.go", SLICE_TARGETS[name])
        rebuild_binary()
        yield
    finally:
        for mod, content in originals.items():
            SLICE_TARGETS[mod].write_text(content, encoding="utf-8")
        rebuild_binary()


@contextmanager
def runtime_session():
    stop_daemon()
    reset_state()
    start_daemon()
    try:
        yield
    finally:
        stop_daemon()


@contextmanager
def seeded_runtime(seed: str):
    prior = os.environ.get("VERIFIER_SEED")
    os.environ["VERIFIER_SEED"] = seed
    try:
        with runtime_session():
            yield
    finally:
        if prior is None:
            os.environ.pop("VERIFIER_SEED", None)
        else:
            os.environ["VERIFIER_SEED"] = prior
