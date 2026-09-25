#!/usr/bin/env bash
# Stage parsed manifest rows to /app/state for downstream resolution.

staging_commit_parsed() {
  local parsed_file="$1"
  local state_dir="/app/state"
  local staging_path="${state_dir}/parsed-manifest.tsv"
  local meta_path="${state_dir}/staging-meta.json"
  mkdir -p "${state_dir}"
  cp "${parsed_file}" "${staging_path}"
  local digest line_count
  digest="$(sha256sum "${staging_path}" | awk '{print $1}')"
  line_count="$(wc -l < "${staging_path}" | tr -d ' ')"
  python3 - "${meta_path}" "${digest}" "${line_count}" <<'PY'
import json
import sys

path, digest, lines = sys.argv[1], sys.argv[2], int(sys.argv[3])
with open(path, "w", encoding="utf-8") as fh:
    json.dump(
        {"staging_version": 1, "parsed_sha256": digest, "line_count": lines},
        fh,
        indent=2,
        sort_keys=True,
    )
    fh.write("\n")
PY
}
