from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def audit_digest(summary: dict[str, int], lineage: list[str]) -> str:
    chain_json = json.dumps(lineage, separators=(",", ":"))
    body = (
        f'{{"custody_depth":{summary["custody_depth"]},'
        f'"duplicate_count":{summary["duplicate_count"]},'
        f'"lineage":{chain_json},'
        f'"loan_conflicts":{summary["loan_conflict_count"]}}}'
    )
    return hashlib.sha256(body.encode()).hexdigest()


def write_dossier(path: str, rep: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
