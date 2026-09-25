#!/usr/bin/env bash
# String table resolution for SRCDEM files.

sd_load_strings() {
  local demo="$1"
  local out_ndjson="$2"
  python3 - <<'PY' "$demo" "$out_ndjson"
import struct, sys
from pathlib import Path
demo = Path(sys.argv[1])
out = Path(sys.argv[2])
data = demo.read_bytes()
_, _, sc, _, sio, _, _ = struct.unpack_from("<IHHIIII", data, 8)
strings = []
for i in range(sc):
    (off,) = struct.unpack_from("<I", data, sio + i * 4)
    end = data.index(0, off)
    strings.append(data[off:end].decode("utf-8"))
import json
with out.open("w", encoding="utf-8") as f:
    for idx, s in enumerate(strings):
        f.write(json.dumps({"idx": idx, "text": s}) + "\n")
PY
}

sd_resolve_string() {
  local strings_ndjson="$1"
  local str_byte="$2"
  local idx="$str_byte"
  if (( str_byte > 127 )); then
    idx=$(( str_byte - 256 ))
  fi
  python3 - <<'PY' "$strings_ndjson" "$idx"
import json, sys
path, idx = sys.argv[1], int(sys.argv[2])
for line in open(path, encoding="utf-8"):
    rec = json.loads(line)
    if rec["idx"] == idx:
        print(rec["text"])
        break
else:
    print("")
PY
}
