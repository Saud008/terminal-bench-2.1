#!/usr/bin/env bash
# XML path helpers for primary and repomd parsers.
xml_local_name() {
  python3 - "$1" <<'PY'
import sys
tag = sys.argv[1]
if "}" in tag:
    print(tag.split("}", 1)[1])
else:
    print(tag)
PY
}
