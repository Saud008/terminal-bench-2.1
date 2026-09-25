"""Reference SHA-256 digest helper mirroring peskin_pq audit_digest (env-side contract)."""
import hashlib
import json


def atlas_audit_digest(bag_id: str, drop_count: int, sync_pair_count: int, topics: list[str]) -> str:
    body = json.dumps(
        {
            "bag_id": bag_id,
            "drop_count": drop_count,
            "sync_pair_count": sync_pair_count,
            "topics": sorted(topics),
        },
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode()).hexdigest()
