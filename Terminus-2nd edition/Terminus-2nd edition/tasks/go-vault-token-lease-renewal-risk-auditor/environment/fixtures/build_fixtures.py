"""Build bundled renewal transcripts and config for vaultaud fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/app/fixtures")

EPOCH_2026 = "2026-01-01T00:00:00Z"


def _rev(effective_from: str, max_ttl_sec: int, parent: str = "", *,
         override_parent: bool = False, deny_renew: bool = False) -> dict:
    return {
        "effective_from": effective_from,
        "max_ttl_sec": max_ttl_sec,
        "parent": parent,
        "override_parent": override_parent,
        "deny_renew": deny_renew,
    }


def digest_dir(base: Path, names: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode("utf-8"))
        digest.update((base / name).read_bytes())
    return digest.hexdigest()


def write_config(base: Path) -> None:
    cfg = base / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    policies = {
        "policies": {
            "base-default": {"revisions": [_rev(EPOCH_2026, 86400)]},
            "ops-standard": {
                "revisions": [
                    _rev(EPOCH_2026, 21600, "base-default"),
                    _rev("2026-03-15T08:20:00Z", 7200, "base-default"),
                ]
            },
            "ci-root": {"revisions": [_rev(EPOCH_2026, 10800)]},
            "ci-deploy": {"revisions": [_rev(EPOCH_2026, 3600, "ci-root")]},
            "break-glass": {
                "revisions": [_rev(EPOCH_2026, 12000, "ci-deploy", override_parent=True)]
            },
            "batch-locked": {
                "revisions": [_rev(EPOCH_2026, 1800, "base-default", deny_renew=True)]
            },
            "locked-child": {"revisions": [_rev(EPOCH_2026, 9000, "batch-locked")]},
        }
    }
    mounts = {
        "mounts": {
            "userpass": {"max_lease_ttl_sec": 43200, "max_token_lifetime_sec": 10800, "renewable": False},
            "approle": {"max_lease_ttl_sec": 1800, "max_token_lifetime_sec": 7200, "renewable": True},
            "kubernetes": {"max_lease_ttl_sec": 21600, "max_token_lifetime_sec": 5400, "renewable": True},
            "oidc": {"max_lease_ttl_sec": 43200, "max_token_lifetime_sec": 43200, "renewable": True},
        }
    }
    roles = {
        "roles": {
            "admin": {"mount": "userpass", "max_ttl_sec": 7200, "max_token_lifetime_sec": 10800, "renewable": True},
            "ci-runner": {"mount": "approle", "max_ttl_sec": 3600, "max_token_lifetime_sec": 7200, "renewable": True},
            "batch": {"mount": "approle", "max_ttl_sec": 600, "max_token_lifetime_sec": 3600, "renewable": False},
            "svc-agent": {"mount": "kubernetes", "max_ttl_sec": 10800, "max_token_lifetime_sec": 5400, "renewable": True},
            "deploy-bot": {"mount": "oidc", "max_ttl_sec": 36000, "max_token_lifetime_sec": 43200, "renewable": True},
        }
    }
    (cfg / "policies.json").write_text(json.dumps(policies, indent=2) + "\n", encoding="utf-8")
    (cfg / "mounts.json").write_text(json.dumps(mounts, indent=2) + "\n", encoding="utf-8")
    (cfg / "roles.json").write_text(json.dumps(roles, indent=2) + "\n", encoding="utf-8")
    (cfg / "audit_anchor.txt").write_text("2026-03-15T09:04:00Z\n", encoding="utf-8")


def _event(event_id: str, token_id: str, parent_id: str, seq: int, mount: str, role: str,
           policies: list[str], lease: int, issued: str, *, renewable: bool = True,
           orphan: bool = False) -> dict:
    return {
        "event_id": event_id,
        "token_id": token_id,
        "parent_id": parent_id,
        "renewal_seq": seq,
        "mount": mount,
        "role": role,
        "policy_names": policies,
        "lease_ttl_sec": lease,
        "renewable": renewable,
        "orphan": orphan,
        "issued_at": issued,
    }


def write_transcripts(base: Path) -> None:
    tdir = base / "renewal_logs"
    tdir.mkdir(parents=True, exist_ok=True)
    alpha = [
        _event("ev-alpha-1", "hvs.ROOT", "", 1, "userpass", "admin",
               ["base-default", "ops-standard"], 7200, "2026-03-15T08:00:00Z"),
        _event("ev-alpha-2", "hvs.CHILD", "hvs.ROOT", 1, "userpass", "admin",
               ["ops-standard"], 7000, "2026-03-15T08:30:00Z"),
        _event("ev-alpha-3", "hvs.CHILD", "hvs.ROOT", 2, "userpass", "admin",
               ["ops-standard"], 9000, "2026-03-15T09:00:00Z"),
    ]
    bravo = [
        _event("ev-bravo-1", "hvs.SVC", "", 1, "kubernetes", "svc-agent",
               ["ops-standard"], 20000, "2026-03-15T08:40:00Z"),
        _event("ev-bravo-2", "hvs.CI", "", 1, "approle", "ci-runner",
               ["ci-root", "ci-deploy"], 7200, "2026-03-15T08:50:00Z"),
        _event("ev-bravo-3", "hvs.CI", "", 2, "approle", "ci-runner",
               ["ci-root", "ci-deploy"], 900, "2026-03-15T08:55:00Z"),
    ]
    charlie = [
        _event("ev-charlie-1", "hvs.BATCH", "hvs.SVC", 1, "approle", "batch",
               ["batch-locked"], 1200, "2026-03-15T08:59:00Z"),
        _event("ev-charlie-2", "hvs.ORPH", "hvs.MISSING", 1, "approle", "batch",
               ["ci-root"], 1200, "2026-03-15T08:58:00Z"),
        _event("ev-charlie-3", "hvs.SEV", "hvs.ROOT", 1, "kubernetes", "svc-agent",
               ["ci-deploy"], 4000, "2026-03-15T09:01:00Z", orphan=True),
        _event("ev-charlie-4", "hvs.DENY", "", 1, "approle", "batch",
               ["ci-root"], 600, "2026-03-15T07:00:00Z"),
        _event("ev-charlie-5", "hvs.DENY", "", 2, "approle", "batch",
               ["ci-root"], 600, "2026-03-15T08:05:00Z"),
        _event("ev-charlie-6", "hvs.DCHILD", "hvs.DENY", 1, "approle", "ci-runner",
               ["ci-deploy"], 900, "2026-03-15T08:30:00Z"),
    ]
    for name, rows in (("alpha", alpha), ("bravo", bravo), ("charlie", charlie)):
        path = tdir / f"{name}.lease-renew.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def main() -> None:
    write_config(ROOT)
    write_transcripts(ROOT)
    cfg_digest = digest_dir(
        ROOT / "config", ("policies.json", "mounts.json", "roles.json", "audit_anchor.txt")
    )
    tdir = ROOT / "renewal_logs"
    tr_digest = digest_dir(tdir, tuple(sorted(p.name for p in tdir.glob("*.lease-renew.jsonl"))))
    print(f"fixtures built under {ROOT} config={cfg_digest} transcripts={tr_digest}")


if __name__ == "__main__":
    main()
