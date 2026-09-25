#!/usr/bin/env python3
"""Apply oracle patches for municipal-permit-inspection-queue."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ROOT / "files"
MAP = {
    "permit_fix_cred_floor.go": "credmatch/cred_floor.go",
    "permit_fix_hold_mask.go": "districtgate/hold_mask.go",
    "permit_fix_calendar_span.go": "calendarblock/calendar_span.go",
    "permit_fix_violation_prior.go": "priorscore/violation_prior.go",
    "permit_fix_lane_router.go": "laneassign/lane_router.go",
    "permit_fix_emit_manifest.go": "manifestemit/emit_manifest.go",
    "permit_fix_rank_permits.go": "rankengine/rank_permits.go",
}


def main() -> None:
    app_internal = Path("/app/internal")
    for src_name, rel in MAP.items():
        shutil.copy2(FILES / src_name, app_internal / rel)
    print("oracle patches applied")


if __name__ == "__main__":
    main()
