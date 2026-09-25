#!/usr/bin/env bash
# Reference solution for the wavehold hold-preview gates.
#
# Each of the six baseline gate modules under /app/lib/meridian/gates ships as
# a stub that hard-codes the wrong rollout decision. This script rewrites every
# module in place with its corrected body, then recompiles the gate bytecode so
# the next preview run loads the repaired policy. The corrected sources are
# emitted inline (here-documents) rather than copied, so this file is the sole,
# self-contained record of the fix.
set -euo pipefail

GATES_DIR=/app/lib/meridian/gates

cat > "$GATES_DIR/deny_pin_hold.py" <<'WAVEHOLD_GATE'
"""Gate: deny-pin hold — policy hold on pinned attrs. See /app/docs/deny-pin-hold.md."""

from __future__ import annotations

from typing import List


def attr_is_held(attr: str, hold_attrs: List[str]) -> bool:
    return any(attr == pinned for pinned in hold_attrs)
WAVEHOLD_GATE

cat > "$GATES_DIR/identity_bind.py" <<'WAVEHOLD_GATE'
"""Gate: identity-bind preview — blank-node upsert binding. See /app/docs/identity-bind-preview.md."""

from __future__ import annotations

from typing import Any, Dict, List


def _sort_facets(facets: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(facets, key=lambda f: (f.get("key", ""), f.get("value", "")))


def _facets_equal(a: List[Dict[str, str]], b: List[Dict[str, str]]) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x.get("key") != y.get("key") or x.get("value") != y.get("value"):
            return False
    return True


def _node_matches(g: Any, uid: str, keys: List[Dict[str, Any]]) -> bool:
    for key in keys:
        val, ok = g.get_scalar(uid, key["attr"])
        if not ok or val != key["value"]:
            return False
        kf = key.get("facets") or []
        if kf:
            stored = _sort_facets(g.get_facets(uid, key["attr"]))
            want = _sort_facets(kf)
            if not _facets_equal(stored, want):
                return False
    return True


def resolve_bind(g: Any, edit: Dict[str, Any]) -> str:
    if not edit.get("bind") or not edit.get("bind_on"):
        return g.resolve_node(edit["node"])
    for uid in g.uids_sorted():
        if _node_matches(g, uid, edit["bind_on"]):
            g.bind_blank(edit["node"], uid)
            return uid
    return g.resolve_node(edit["node"])
WAVEHOLD_GATE

cat > "$GATES_DIR/conflict_precedence.py" <<'WAVEHOLD_GATE'
"""Gate: conflict-precedence hold — same node/attr precedence winner. See /app/docs/conflict-precedence-hold.md."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def resolve_precedence(pending: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str], List[int]] = {}
    for i, w in enumerate(pending):
        if w["multi"]:
            continue
        groups.setdefault((w["uid"], w["attr"]), []).append(i)

    winner: Dict[Tuple[str, str], int] = {}
    for k, idxs in groups.items():
        best = idxs[0]
        for i in idxs[1:]:
            if pending[i]["edit_rank"] >= pending[best]["edit_rank"]:
                best = i
        winner[k] = best

    out: List[Dict[str, Any]] = []
    for i, w in enumerate(pending):
        if w["multi"]:
            out.append({"edit": w, "reason": "list_coalesce", "winner": True})
            continue
        k = (w["uid"], w["attr"])
        if len(groups[k]) == 1:
            out.append({"edit": w, "reason": "commit_admit", "winner": True})
        elif winner[k] == i:
            out.append({"edit": w, "reason": "precedence_winner", "winner": True})
        else:
            out.append({"edit": w, "reason": "precedence_loser", "winner": False})
    return out
WAVEHOLD_GATE

cat > "$GATES_DIR/list_coalesce.py" <<'WAVEHOLD_GATE'
"""Gate: list-coalesce — list entry distinctness. See /app/docs/list-coalesce-rules.md."""

from __future__ import annotations

from typing import Dict, List, Tuple


def coalesce_entry(
    existing: List[Dict[str, str]], add: Dict[str, str]
) -> Tuple[List[Dict[str, str]], bool]:
    for e in existing:
        if e["value"] == add["value"] and e.get("lang", "") == add.get("lang", ""):
            return existing, False
    return existing + [add], True
WAVEHOLD_GATE

cat > "$GATES_DIR/preflight_hold.py" <<'WAVEHOLD_GATE'
"""Gate: preflight hold — @if preconditions on live state. See /app/docs/preflight-hold-rules.md."""

from __future__ import annotations

from typing import Any, Dict

ROOT_NODE = "0xroot"


def preflight_ok(g: Any, rec: Dict[str, Any]) -> bool:
    for c in rec.get("preconds") or []:
        val, ok = g.get_scalar(ROOT_NODE, c["attr"])
        if not ok:
            return False
        if c.get("op") == "eq":
            if val != c["value"]:
                return False
        else:
            return False
    return True
WAVEHOLD_GATE

cat > "$GATES_DIR/schema_bump_abort.py" <<'WAVEHOLD_GATE'
"""Gate: schema-bump abort — commit/abort of writes + schema marks. See /app/docs/schema-bump-abort.md."""

from __future__ import annotations

from typing import Any, Dict


def keep_commit(rec: Dict[str, Any]) -> bool:
    return bool(rec.get("commit", False))
WAVEHOLD_GATE

rm -rf "$GATES_DIR/__pycache__"
python3 -c "import compileall; compileall.compile_dir('$GATES_DIR', quiet=1)"

# Self-check: a fully corrected pipeline seals a non-empty atlas whose digest
# field is populated under the expected schema string.
bash /app/scripts/reset-state.sh
wavehold scan --wave /app/fixtures/waves/wave-merged.jsonl --run-id ref-selfcheck >/dev/null
wavehold compile --run-id ref-selfcheck >/dev/null
wavehold publish --run-id ref-selfcheck --output /app/output/mutation-rollout-atlas.json >/dev/null
python3 - <<'PY'
import json
atlas = json.load(open("/app/output/mutation-rollout-atlas.json"))
assert atlas.get("atlas_digest"), "atlas digest missing"
assert atlas.get("schema") == "wavehold.rollout.v1", "unexpected atlas schema"
PY
