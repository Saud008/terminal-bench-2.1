"""
Independent PAM stack replay reference for verifier anti-cheat.

Implements contracts from /app/docs without importing /app/lib.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_INCLUDE_DEPTH = 8
PHASE_ORDER = ("auth", "account", "password", "session")
APP_ROOT = Path("/app")
STACKS_ROOT = APP_ROOT / "fixtures" / "stacks"


@dataclass
class AuditRow:
    seq: int
    phase: str
    module: str
    control: str
    rc: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "phase": self.phase,
            "module": self.module,
            "control": self.control,
            "rc": self.rc,
        }


@dataclass
class ReplayResult:
    stack: str
    user: str
    exit_code: int
    phases: list[dict[str, Any]]
    environment: dict[str, str]
    audit: list[AuditRow]
    audit_path: str

    def export_doc(self) -> dict[str, Any]:
        return {
            "stack": self.stack,
            "user": self.user,
            "exit_code": self.exit_code,
            "phases": self.phases,
            "environment": self.environment,
            "audit_path": self.audit_path,
        }


def audit_path_for(export_path: str) -> str:
    if export_path.endswith(".json"):
        return export_path[:-5] + ".audit.jsonl"
    return export_path + ".audit.jsonl"


def is_env_module(module: str) -> bool:
    return Path(module).name.startswith("pam_env")


def flatten_stack(stack_file: Path) -> list[dict[str, Any]]:
    def load_entries(path: Path, depth: int) -> list[dict[str, Any]]:
        if depth > MAX_INCLUDE_DEPTH:
            raise ValueError("include depth exceeded")
        data = json.loads(path.read_text(encoding="utf-8"))
        out: list[dict[str, Any]] = []
        for entry in data.get("entries", []):
            if "include" in entry:
                rel = entry["include"]
                inc_path = STACKS_ROOT / rel
                if not inc_path.is_file():
                    raise FileNotFoundError(rel)
                out.extend(load_entries(inc_path, depth + 1))
            else:
                out.append(entry)
        return out

    return load_entries(stack_file, 1)


def run_stub(module: str, phase: str, user: str, args: list[str]) -> int:
    mod_path = APP_ROOT / module
    if not mod_path.is_file():
        return 127
    env = os.environ.copy()
    env["PAM_USER"] = user
    env["PAM_PHASE"] = phase
    proc = subprocess.run(
        ["bash", str(mod_path), *args],
        cwd=str(APP_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return int(proc.returncode)


def replay_stack(stack_path: str, user: str, export_path: str) -> ReplayResult:
    stack_file = Path(stack_path)
    entries = flatten_stack(stack_file)
    env: dict[str, str] = {}
    pending_auth: list[tuple[str, str]] = []
    snapshot = dict(env)
    audit: list[AuditRow] = []
    phases_out: list[dict[str, Any]] = []
    exit_code = 0
    seq = 0

    def record(phase: str, module: str, control: str, rc: int) -> None:
        nonlocal seq
        seq += 1
        audit.append(AuditRow(seq, phase, module, control, rc))

    def apply_env(phase: str, args: list[str]) -> None:
        nonlocal pending_auth
        for raw in args:
            if "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            if phase == "auth":
                pending_auth.append((key, value))
            else:
                env[key] = value

    def commit_auth() -> None:
        nonlocal pending_auth
        for key, value in pending_auth:
            env[key] = value
        pending_auth = []

    def discard_auth_pending() -> None:
        nonlocal pending_auth
        pending_auth = []

    def rollback() -> None:
        nonlocal env
        env = dict(snapshot)

    for phase in PHASE_ORDER:
        phase_entries = [e for e in entries if e.get("phase") == phase]
        if not phase_entries:
            continue

        failed = False
        modules_run = 0
        for entry in phase_entries:
            module = entry["module"]
            control = entry["control"]
            args = list(entry.get("args", []))
            rc = 0

            if is_env_module(module):
                apply_env(phase, args)
                record(phase, module, control, 0)
            else:
                rc = run_stub(module, phase, user, args)
                record(phase, module, control, rc)

            modules_run += 1

            if control == "optional":
                pass
            elif control == "sufficient":
                if rc == 0 and not failed:
                    break
            elif control == "requisite":
                if rc != 0:
                    failed = True
                    break
            elif control == "required":
                if rc != 0:
                    failed = True

        status = "fail" if failed else "ok"
        phases_out.append({"phase": phase, "status": status, "modules_run": modules_run})

        if phase == "auth":
            if status == "ok":
                commit_auth()
            else:
                discard_auth_pending()

        if status == "fail":
            exit_code = 1
            break

    audit_target = audit_path_for(export_path)
    if exit_code != 0:
        rollback()
        write_audit(audit_target, audit)

    return ReplayResult(
        stack=stack_path,
        user=user,
        exit_code=exit_code,
        phases=phases_out,
        environment=dict(env),
        audit=audit if exit_code != 0 else audit,
        audit_path=audit_target,
    )


def write_audit(path: str, rows: list[AuditRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row.to_dict(), separators=(",", ":")) + "\n")


def read_audit(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
