#!/usr/bin/env bash
# Shared helpers for demo-index.

sd_require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing command: $1" >&2
    exit 1
  }
}

sd_norm_rel() {
  local root="$1" path="$2"
  local rel="${path#"${root%/}"/}"
  rel="${rel//\\//}"
  printf '%s' "$rel"
}

sd_arg_mask() {
  local seed="$1" source="$2"
  python3 - <<'PY' "$seed" "$source"
import hashlib, sys
seed, source = sys.argv[1:3]
h = hashlib.sha256(f"{seed}:{source}:arg".encode()).hexdigest()
print(int(h[:8], 16))
PY
}

sd_read_header() {
  local demo="$1"
  python3 - <<'PY' "$demo"
import struct, sys
from pathlib import Path
p = Path(sys.argv[1])
data = p.read_bytes()
if data[:6] != b"SRCDEM":
    raise SystemExit(1)
if data[6] != 1:
    raise SystemExit(1)
flags = data[7]
signon, tc, sc, plen, sio, tio, poff = struct.unpack_from("<IHHIIII", data, 8)
print(flags, signon, tc, sc, plen, sio, tio, poff)
PY
}
