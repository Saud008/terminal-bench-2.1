"""HTTP helpers for kongadmit verifier suites."""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

APP = Path("/app")
CONFIG = APP / "config" / "gateway.json"
CLI = Path("/usr/local/bin/kongadmit")
PROXY = "http://127.0.0.1:8000"
ADMIN = "http://127.0.0.1:8001"


def rebuild() -> None:
    proc = subprocess.run(
        ["bash", str(APP / "scripts" / "verifier-rebuild.sh")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def stop_daemon() -> None:
    subprocess.run(["pkill", "-x", "kongadmit"], check=False)
    time.sleep(0.25)


def start_daemon() -> None:
    stop_daemon()
    subprocess.Popen(
        [str(CLI), "serve", "--config", str(CONFIG)],
        cwd=APP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen(f"{ADMIN}/health", timeout=0.5)
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("kongadmit did not start")


def admin_post(path: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{ADMIN}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def admin_get(path: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(f"{ADMIN}{path}", timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def proxy_request(
    method: str,
    path: str,
    *,
    api_key: str = "",
    bearer: str = "",
) -> tuple[int, dict[str, str], bytes]:
    headers = {}
    if api_key:
        headers["X-Api-Key"] = api_key
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(f"{PROXY}{path}", headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            hdrs = {k: v for k, v in resp.headers.items()}
            return resp.status, hdrs, resp.read()
    except urllib.error.HTTPError as exc:
        hdrs = {k: v for k, v in exc.headers.items()}
        return exc.code, hdrs, exc.read()


def ingest_deck(path: Path) -> tuple[int, dict]:
    return admin_post("/admin/ingest", {"deck_path": str(path)})


def reset_rates() -> None:
    admin_post("/admin/reset-rates")
