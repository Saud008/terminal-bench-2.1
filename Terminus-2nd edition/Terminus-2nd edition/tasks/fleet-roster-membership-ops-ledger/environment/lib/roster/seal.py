from __future__ import annotations

import sys

sys.path.insert(0, "/app/fixtures")
from digest_util import sha256_canonical_json


def compute_membership_seal(st: dict) -> str:
    # BUG: missing membership_epoch; queue_states may be unsorted
    body = {
        "cluster": st["cluster"],
        "commit_index": st["commit_index"],
        "current_term": st["current_term"],
        "leader_id": st["leader_id"],
        "membership": list(st["membership"]),
        "queue_states": dict(st["queue_states"]),
    }
    return sha256_canonical_json(body)
