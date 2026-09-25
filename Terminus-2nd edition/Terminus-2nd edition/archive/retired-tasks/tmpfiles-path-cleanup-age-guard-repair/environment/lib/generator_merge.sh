#!/usr/bin/env bash

merge_fragments() {
  local frag_dir="$1"
  local mode="$2"
  python3 - "$frag_dir" "$mode" <<'PY'
import json, os, sys

frag_dir, mode = sys.argv[1:3]
lines = []
for name in sorted(os.listdir(frag_dir)):
    if not name.endswith(".conf"):
        continue
    tag = "boot-ex" if ".boot-ex." in name or name.startswith("boot-ex.") else "boot"
    if mode == "boot" and tag == "boot-ex":
        pass
    elif mode == "boot-ex" and tag == "boot":
        continue
    with open(os.path.join(frag_dir, name), encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line and not line.startswith("#"):
                lines.append(line)
print(json.dumps(lines))
PY
}

write_merged_rules() {
  local frag_dir="$1"
  local mode="$2"
  local out="$3"
  local tmp_json
  tmp_json="$(mktemp)"
  merge_fragments "$frag_dir" "$mode" > "${tmp_json}"
  python3 - "${out}" "${tmp_json}" <<'PY'
import json, sys
out_path, json_path = sys.argv[1:3]
with open(json_path, encoding="utf-8") as fh:
    lines = json.load(fh)
with open(out_path, "w", encoding="utf-8") as fh:
    if lines:
        fh.write("\n".join(lines) + "\n")
PY
  rm -f "${tmp_json}"
}
