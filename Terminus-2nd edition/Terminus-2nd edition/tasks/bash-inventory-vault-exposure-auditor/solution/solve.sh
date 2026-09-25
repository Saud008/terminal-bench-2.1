#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

python3 <<'PY'
from pathlib import Path

Path("/app/lib/group_policy.py").write_text(
    """\"\"\"Canonical runtime policy for lineage expansion and precedence order.\"\"\"

from __future__ import annotations

CHILDREN_FIRST = True
HOST_BEFORE_GROUPS = False


def host_group_flags() -> tuple[bool, bool]:
    \"\"\"Return the scan-time lineage and precedence switches.\"\"\"
    return CHILDREN_FIRST, HOST_BEFORE_GROUPS


def lineage_policy_summary() -> dict[str, bool]:
    \"\"\"Expose the policy in a structured form for smoke checks.\"\"\"
    return {
        \"children_first\": CHILDREN_FIRST,
        \"host_before_groups\": HOST_BEFORE_GROUPS,
    }
""",
    encoding="utf-8",
)

Path("/app/lib/staging_policy.py").write_text(
    """\"\"\"Canonical staging artifact policy for digest composition and emit behavior.\"\"\"

from __future__ import annotations

import hashlib
import json
from typing import Any

USE_INVENTORY_IGNORE = True
DIGEST_FINDINGS = True
EXPORT_REOPEN = False


def _ndjson_bytes(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b\"\"
    return (
        \"\\n\".join(json.dumps(row, sort_keys=True) for row in rows) + \"\\n\"
    ).encode()


def compute_staging_digest(host_rows: list[dict[str, Any]], findings: list[dict[str, Any]]) -> str:
    \"\"\"Hash staged NDJSON bytes; findings inclusion follows DIGEST_FINDINGS.\"\"\"
    hosts_blob = _ndjson_bytes(host_rows)
    if DIGEST_FINDINGS:
        return hashlib.sha256(hosts_blob + _ndjson_bytes(findings)).hexdigest()
    return hashlib.sha256(hosts_blob).hexdigest()


def emit_reopens_inventory() -> bool:
    \"\"\"The emit stage must reuse staged artifacts and never rescan the tree.\"\"\"
    return EXPORT_REOPEN
""",
    encoding="utf-8",
)

Path("/app/lib/vault_policy.py").write_text(
    """\"\"\"Canonical vault marker handling for inventory values.\"\"\"

from __future__ import annotations

VAULT_PREFIX = \"$ANSIBLE_VAULT;\"


def normalize_vault_value(value: str) -> str:
    \"\"\"Trim transport whitespace before checking the vault marker.\"\"\"
    return value.strip()


def has_vault_prefix(value: str, prefix: str = VAULT_PREFIX) -> bool:
    \"\"\"Return True when the normalized value begins with the vault prefix.\"\"\"
    return normalize_vault_value(value).startswith(prefix)
""",
    encoding="utf-8",
)
PY

bash "${APP_ROOT}/scripts/reset-state.sh"
bash "${APP_ROOT}/scripts/rebuild-hostsatlas.sh"

python3 <<'PY'
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, "/app/lib")
engine = Path("/app/lib/inventory_engine.py")
spec = importlib.util.spec_from_file_location("inventory_engine", engine)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
assert mod.CHILDREN_FIRST is True
assert mod.HOST_BEFORE_GROUPS is False
assert mod.USE_INVENTORY_IGNORE is True
assert mod.DIGEST_FINDINGS is True
assert mod.EXPORT_REOPEN is False
assert mod.vault_policy.has_vault_prefix("  $ANSIBLE_VAULT;1.1;AES256;deadbeef  ")
assert mod.staging_policy.emit_reopens_inventory() is False
print("inventory_engine oracle flags ok")
PY

/usr/local/bin/hostsatlas scan --tree /app/fixtures/trees/clean-tree/tree.json
/usr/local/bin/hostsatlas emit --tree clean-tree --output /app/output/oracle-smoke.json
test -f /app/output/oracle-smoke.json
echo "hostsatlas oracle ready"
