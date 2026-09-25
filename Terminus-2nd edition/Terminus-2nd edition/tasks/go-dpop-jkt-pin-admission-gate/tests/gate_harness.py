"""Shared jktadmit HTTP harness for verifier modules."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

APP = Path("/app")
CONFIG = APP / "config" / "jktadmit.json"
LEDGER = APP / "output" / "deny-ledger.json"
SNAPSHOT = APP / "state" / "chainhead.json"
CLI = Path("/usr/local/bin/jktadmit")
BIN_MIRROR = APP / "bin" / "jktadmit"

OPEN_HTU = "https://jktadmit.local/gate/session/open"
CHECK_HTU = "https://jktadmit.local/gate/proof/check"

SEED = os.environ.get("VERIFIER_SEED", "jktadmit-seed-7")
EXTRA_SEEDS = ("jktadmit-matrix-3", "jktadmit-matrix-19", "jktadmit-matrix-47")

DEFAULT_PIN_DIR = Path("/opt/verifier-fixtures/jktadmit_hidden")

PROTECTED_SHA256: dict[str, str] = {}


def load_protected(digest_map: dict[str, str]) -> None:
    global PROTECTED_SHA256
    PROTECTED_SHA256 = dict(digest_map)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stop_daemon() -> None:
    subprocess.run(["pkill", "-9", "-x", "jktadmit"], check=False)
    time.sleep(0.3)


def start_daemon(env_overrides: dict[str, str] | None = None) -> None:
    stop_daemon()
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    subprocess.Popen(
        [str(CLI), "serve", "--config", str(CONFIG)],
        cwd=APP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    for _ in range(40):
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=0.5)
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("jktadmit did not start")


def http_json(method: str, path: str, body: dict | None = None, now_unix: int | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if now_unix is not None:
        headers["X-Test-Now-Unix"] = str(now_unix)
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


def open_session(principal: str, session: str, dpop_proof: str, *, now_unix: int, expect_ok: bool = True) -> tuple[int, dict]:
    status, body = http_json(
        "POST",
        "/gate/session/open",
        {"principal": principal, "session": session, "dpop_proof": dpop_proof},
        now_unix=now_unix,
    )
    if expect_ok:
        assert status == 200, body
    return status, body


def check_proof(principal: str, session: str, bind_ticket: str, dpop_proof: str, *, now_unix: int) -> tuple[int, dict]:
    status, body = http_json(
        "POST",
        "/gate/proof/check",
        {"principal": principal, "session": session, "bind_ticket": bind_ticket, "dpop_proof": dpop_proof},
        now_unix=now_unix,
    )
    return status, body


def commit(principal: str, session: str) -> dict:
    status, body = http_json("POST", "/gate/audit/commit", {"principal": principal, "session": session})
    assert status == 200, body
    assert LEDGER.is_file()
    return json.loads(LEDGER.read_text(encoding="utf-8"))


@contextmanager
def runtime_session(env_overrides: dict[str, str] | None = None):
    stop_daemon()
    reset_state()
    start_daemon(env_overrides)
    try:
        yield
    finally:
        stop_daemon()


@contextmanager
def seeded_runtime(seed: str, env_overrides: dict[str, str] | None = None):
    prior = os.environ.get("VERIFIER_SEED")
    os.environ["VERIFIER_SEED"] = seed
    try:
        with runtime_session(env_overrides):
            yield
    finally:
        if prior is None:
            os.environ.pop("VERIFIER_SEED", None)
        else:
            os.environ["VERIFIER_SEED"] = prior
