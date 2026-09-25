#!/usr/bin/env bash



staging_path_for() {

  local snap="$1"

  python3 - "$snap" <<'PY'

import sys

from pathlib import Path



snap = Path(sys.argv[1])

print(str(snap.with_suffix(snap.suffix + ".merge-staging.json")))

PY

}



write_merge_staging() {

  local snap="$1"

  local digest

  digest="$(canonical_snapshot_digest "$snap")"

  python3 - "$snap" "$digest" <<'PY'

import json, subprocess, sys

from pathlib import Path



snap = Path(sys.argv[1])

digest = sys.argv[2]

meta = json.loads(snap.read_text(encoding="utf-8"))



def parse_keys(tree: Path, rel: str) -> list[str]:

    cmd = [

        "bash",

        "-c",

        'source /app/lib/common.sh; source /app/lib/parse.sh; parse_fragment "$1"',

        "bash",

        str(tree / rel),

    ]

    parsed = json.loads(subprocess.check_output(cmd, text=True).strip())

    keys: list[str] = []

    for ent in parsed["entries"]:

        if ent["key"] in keys:

            keys.remove(ent["key"])

        keys.append(ent["key"])

    return keys



tree = Path(meta["tree_path"])

layer_keys = []

for rel in meta["processing_order"]:

    layer_keys.append({"file": rel, "keys": parse_keys(tree, rel)})

staging = {

    "staging_version": 1,

    "snapshot_digest": digest,

    "layer_keys": layer_keys,

    "last_file": meta["processing_order"][-1] if meta["processing_order"] else "",

}

staging_path = snap.with_suffix(snap.suffix + ".merge-staging.json")

staging_path.parent.mkdir(parents=True, exist_ok=True)

staging_path.write_text(json.dumps(staging, indent=2) + "\n", encoding="utf-8")

PY

}



validate_merge_staging() {

  local snap="$1"

  local digest

  digest="$(canonical_snapshot_digest "$snap")"

  python3 - "$snap" "$digest" <<'PY'

import json, sys

from pathlib import Path



snap = Path(sys.argv[1])

expected = sys.argv[2]

staging_path = snap.with_suffix(snap.suffix + ".merge-staging.json")

if not staging_path.is_file():

    sys.exit(4)

staging = json.loads(staging_path.read_text(encoding="utf-8"))

if staging.get("snapshot_digest") != expected:

    sys.exit(4)

sys.exit(0)

PY

}



# Legacy helper — not used for merge order.

lexicographic_order() {

  local tree="$1"

  python3 - "$tree" <<'PY'

import json, sys

from pathlib import Path



tree = Path(sys.argv[1])

manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))

drop_ins = sorted(manifest.get("drop_ins", []))

print("\n".join(drop_ins))

PY

}

