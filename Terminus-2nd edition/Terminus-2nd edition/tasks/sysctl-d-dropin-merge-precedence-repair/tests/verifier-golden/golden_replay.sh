#!/usr/bin/env bash



REPLAY_LEDGER="${APP_ROOT:-/app}/state/sysctlmerge.replay.jsonl"



append_replay_record() {

  local snap="$1"

  local digest

  digest="$(canonical_snapshot_digest "$snap")"

  python3 - "$snap" "$digest" "$REPLAY_LEDGER" <<'PY'

import hashlib, json, sys

from pathlib import Path



snap = Path(sys.argv[1])

digest = sys.argv[2]

ledger = Path(sys.argv[3])

meta = json.loads(snap.read_text(encoding="utf-8"))

staging_path = snap.with_suffix(snap.suffix + ".merge-staging.json")

layer_keys_digest = ""

if staging_path.is_file():

    staging = json.loads(staging_path.read_text(encoding="utf-8"))

    layer_keys_digest = hashlib.sha256(

        json.dumps(staging["layer_keys"], sort_keys=True, separators=(",", ":")).encode("utf-8")

    ).hexdigest()

record = {

    "tree": meta["tree"],

    "seed": meta["seed"],

    "snapshot_digest": digest,

    "files_processed": meta["stats"]["files_processed"],

    "layer_keys_digest": layer_keys_digest,

}

ledger.parent.mkdir(parents=True, exist_ok=True)

with ledger.open("a", encoding="utf-8") as fh:

    fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

PY

}



validate_replay_record() {

  local snap="$1"

  local digest

  digest="$(canonical_snapshot_digest "$snap")"

  python3 - "$snap" "$digest" "$REPLAY_LEDGER" <<'PY'

import hashlib, json, sys

from pathlib import Path



snap = Path(sys.argv[1])

expected_digest = sys.argv[2]

ledger = Path(sys.argv[3])

if not ledger.is_file():

    sys.exit(5)

meta = json.loads(snap.read_text(encoding="utf-8"))

staging_path = snap.with_suffix(snap.suffix + ".merge-staging.json")

expected_layer_digest = ""

if staging_path.is_file():

    staging = json.loads(staging_path.read_text(encoding="utf-8"))

    expected_layer_digest = hashlib.sha256(

        json.dumps(staging["layer_keys"], sort_keys=True, separators=(",", ":")).encode("utf-8")

    ).hexdigest()

tree = meta["tree"]

seed = meta["seed"]

match = None

for line in ledger.read_text(encoding="utf-8").splitlines():

    if not line.strip():

        continue

    rec = json.loads(line)

    if rec.get("tree") == tree and rec.get("seed") == seed:

        match = rec

if match is None:

    sys.exit(5)

if match.get("snapshot_digest") != expected_digest:

    sys.exit(5)

if match.get("files_processed") != meta["stats"]["files_processed"]:

    sys.exit(5)

if match.get("layer_keys_digest") != expected_layer_digest:

    sys.exit(5)

sys.exit(0)

PY

}

