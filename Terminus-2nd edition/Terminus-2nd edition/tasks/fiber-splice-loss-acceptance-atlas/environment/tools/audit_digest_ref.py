"""Reference SHA-256 digest helper mirroring atlas_emit audit_digest (env-side contract)."""
import hashlib
import json


def atlas_audit_digest(
    run_id: str,
    event_count: int,
    accepted_segment_count: int,
    segment_ids: list[str],
) -> str:
    body = json.dumps(
        {
            "run_id": run_id,
            "event_count": event_count,
            "accepted_segment_count": accepted_segment_count,
            "segment_ids": sorted(segment_ids),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()
