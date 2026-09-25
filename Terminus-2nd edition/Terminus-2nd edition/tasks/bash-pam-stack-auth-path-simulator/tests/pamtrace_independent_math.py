"""Independent contract math for PAM stack simulation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def parse_lines(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            rows.append({"kind": "directive", "text": line})
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        rows.append(
            {
                "kind": "module",
                "type": parts[0],
                "control": parts[1],
                "module": parts[2],
                "args": parts[3:],
            }
        )
    return rows


def reference_expand_service(path: Path) -> list[dict]:
    def expand_file(p: Path, base: Path) -> list[dict]:
        out: list[dict] = []
        for row in parse_lines(p):
            if row["kind"] == "directive":
                text = row["text"]
                if text.startswith(("@include ", "@include-substack ")):
                    inc = text.split(None, 1)[1].strip()
                    inc_path = (base / inc).resolve()
                    out.extend(expand_file(inc_path, inc_path.parent))
                continue
            out.append(row)
        return out

    return expand_file(path, path.parent)


def mod_base(name: str) -> str:
    return name.split("/")[-1]


def lookup_outcome(outcomes: dict, module: str, subject: str) -> int:
    table = outcomes.get(mod_base(module)) or outcomes.get(module) or {}
    raw = table.get(subject, table.get("*", 0))
    mapping = {
        "success": 0,
        "ignore": 1,
        "auth_err": 2,
        "cred_insufficient": 4,
        "perm_denied": 6,
        "acct_expired": 7,
        "user_unknown": 9,
    }
    if isinstance(raw, str):
        return mapping.get(raw, 16)
    return int(raw)


def result_name(code: int) -> str:
    return {
        0: "success",
        1: "ignore",
        2: "auth_err",
        4: "cred_insufficient",
        6: "perm_denied",
        7: "acct_expired",
        9: "user_unknown",
    }.get(code, "unknown")


def reference_walk_auth(modules: list[dict], outcomes: dict, subject: str) -> dict:
    steps = []
    required_failed = False
    first_required_code = 0
    final_code = 0
    final_reason = "ok"
    short_circuited = False
    auth_modules = [m for m in modules if m.get("type") == "auth"]
    for idx, mod in enumerate(auth_modules):
        code = lookup_outcome(outcomes, mod["module"], subject)
        step = {
            "index": idx,
            "module": mod["module"],
            "control": mod["control"],
            "result_code": code,
            "result": result_name(code),
        }
        steps.append(step)
        if short_circuited:
            continue
        control = mod["control"]
        if control == "requisite" and code != 0:
            final_code = code
            final_reason = "requisite_failure"
            short_circuited = True
            continue
        if control == "required" and code != 0:
            required_failed = True
            if first_required_code == 0:
                first_required_code = code
        if control == "sufficient" and code == 0 and not required_failed:
            final_code = 0
            final_reason = "sufficient_success"
            short_circuited = True
    if not short_circuited:
        if required_failed:
            final_code = first_required_code
            final_reason = "required_failure"
        else:
            final_code = 0
            final_reason = "ok"
    return {
        "steps": steps,
        "verdict_code": final_code,
        "verdict": result_name(final_code),
        "reason": final_reason,
    }


def reference_subject_groups(subjects: dict, subject: str) -> list[str]:
    users = subjects.get("users", {})
    groups = subjects.get("groups", {})

    def member_closure(name: str, seen: set[str] | None = None) -> set[str]:
        seen = seen or set()
        if name in seen:
            return set()
        seen.add(name)
        out = {name}
        for child in groups.get(name, []):
            if child in groups:
                out |= member_closure(child, seen)
            else:
                out.add(child)
        return out

    direct = users.get(subject, {}).get("groups", [])
    effective: set[str] = set(direct) | {subject}
    for g in direct:
        effective |= member_closure(g)
    changed = True
    while changed:
        changed = False
        for gname, members in groups.items():
            if gname in effective:
                continue
            if any(m in effective for m in members):
                effective.add(gname)
                changed = True
    return sorted(effective)


def reference_build_ledger(scenario_dir: Path, run_id: str, scenario_name: str) -> dict:
    services = {}
    for svc_file in sorted((scenario_dir / "services").glob("*")):
        if not svc_file.is_file():
            continue
        expanded = reference_expand_service(svc_file)
        auth_modules = [m for m in expanded if m.get("kind") == "module" and m.get("type") == "auth"]
        fp = hashlib.sha256(json.dumps(auth_modules, sort_keys=True).encode()).hexdigest()
        services[svc_file.name] = {
            "service": svc_file.name,
            "modules": auth_modules,
            "service_fingerprint": fp,
        }
    body = {
        "run_id": run_id,
        "scenario": scenario_name,
        "services": services,
        "outcomes": json.loads((scenario_dir / "modules.json").read_text(encoding="utf-8")),
        "subjects": json.loads((scenario_dir / "subjects.json").read_text(encoding="utf-8")),
    }
    fp_src = json.dumps(
        {"run_id": run_id, "services": {k: v["service_fingerprint"] for k, v in services.items()}},
        sort_keys=True,
    )
    body["ledger_fingerprint"] = hashlib.sha256(fp_src.encode()).hexdigest()
    return body


def reference_expected_trace(scenario_dir: Path, run_id: str, scenario_name: str, service: str, subject: str) -> dict:
    ledger_doc = reference_build_ledger(scenario_dir, run_id, scenario_name)
    svc = ledger_doc["services"][service]
    walk = reference_walk_auth(svc["modules"], ledger_doc["outcomes"], subject)
    groups = reference_subject_groups(ledger_doc["subjects"], subject)
    report = {
        "run_id": run_id,
        "service": service,
        "subject": subject,
        "subject_groups": groups,
        "steps": walk["steps"],
        "verdict_code": walk["verdict_code"],
        "verdict": walk["verdict"],
        "reason": walk["reason"],
    }
    digest_src = json.dumps(
        {"service": service, "subject": subject, "steps": walk["steps"], "verdict": walk["verdict"]},
        sort_keys=True,
    )
    report["trace_digest"] = hashlib.sha256(digest_src.encode()).hexdigest()
    return report
