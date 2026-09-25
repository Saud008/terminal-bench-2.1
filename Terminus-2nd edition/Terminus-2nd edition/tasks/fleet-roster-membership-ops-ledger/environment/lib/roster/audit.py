from __future__ import annotations

import json
from pathlib import Path

from roster.staging import DEFAULT_PATH, read_staging


def write_audit(cluster: str, scenario: str) -> None:
    st = read_staging(DEFAULT_PATH)
    report = {
        "cluster": cluster,
        "scenario": scenario,
        "member_count": len(st["membership"]),
        "voter_ids": list(st["membership"]),
        "finding_count": len(st["membership"]),
    }
    out = Path("/app/work/replica-membership-report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
