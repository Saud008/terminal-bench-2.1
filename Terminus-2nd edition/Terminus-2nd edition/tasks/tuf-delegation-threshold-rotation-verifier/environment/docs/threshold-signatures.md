# Threshold signatures

Each metadata file carries a signatures array of keyid and sig hex pairs.

Quorum rules:

1. Resolve the verifying role (root, targets, or snapshot-as-targets) and read its threshold and keyids list from the appropriate signed section or root roles map.
2. A signature counts only when the HMAC-SHA256 digest matches canonical signed bytes using the keyval.public hex decoded as raw key bytes.
3. Each keyid may contribute at most once toward the threshold even if duplicated in the signatures array.
4. Only keyids listed for the verifying role are eligible counters.
5. rotation_ok requires every metadata file in the bundle to meet its role threshold after temporal and reuse filtering.
