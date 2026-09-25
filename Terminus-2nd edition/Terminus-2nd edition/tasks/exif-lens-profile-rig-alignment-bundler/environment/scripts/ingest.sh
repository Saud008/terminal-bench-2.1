#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/core/common.sh"
source "${APP_ROOT}/lib/staging/staging_io.sh"

exif=""
mount=""
while [ $# -gt 0 ]; do
  case "$1" in
    --exif) exif="$2"; shift 2 ;;
    --mount) mount="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${exif}" ] && [ -n "${mount}" ] || die "ingest requires --exif and --mount"
require_file "${exif}"
require_file "${mount}"

captures="$(python3 - "${exif}" <<'PY'
import json, sys
out = []
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if line:
        out.append(json.loads(line))
print(json.dumps(out, separators=(",", ":")))
PY
)"
digest="$(compute_captures_digest "${exif}")"
mhash="$(mount_sha256 "${mount}")"
gen="$(bump_staging_seq "${STAGING_SEQ_PATH}")"

python3 - "${STAGING_PATH}" "${captures}" "${digest}" "${mhash}" "${mount}" "${gen}" <<'PY'
import json, sys
out, caps, digest, mhash, mount, gen = sys.argv[1:7]
doc = {
    "captures": json.loads(caps),
    "captures_digest": digest,
    "mount_sha256": mhash,
    "mount_path": mount,
    "staging_generation": int(gen),
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
