#!/usr/bin/env bash
set -euo pipefail

# Ingest validates bundle manifests before merge writes staging artifacts.
bundle_root="${1:-}"
[[ -n "$bundle_root" && -f "${bundle_root}/manifest.json" ]] || {
  echo "ingest: missing bundle manifest" >&2
  exit 1
}
python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "${bundle_root}/manifest.json" >/dev/null
