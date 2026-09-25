#!/usr/bin/env bash

source /app/lib/common.sh

parse_repomd_revision() {
  local repomd="$1"
  python3 - "$repomd" <<'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
rev = root.find("{http://linux.duke.edu/metadata/repo}revision")
print(rev.text if rev is not None else "")
PY
}

verify_data_checksum() {
  local repo_root="$1"
  local href="$2"
  local expected="$3"
  local ctype="$4"
  local file="${repo_root}/${href}"
  local actual=""
  if [[ "$ctype" == "sha256" ]]; then
    actual="$(sha256_file "$file")"
  else
    actual="$(sha1_file "$file")"
  fi
  [[ "$actual" == "$expected" ]]
}

verify_repomd_checksums() {
  local repo_root="$1"
  local repomd="${repo_root}/repodata/repomd.xml"
  local ok=1
  while IFS= read -r row; do
    [[ -n "$row" ]] || continue
    local href expected ctype
    href="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["href"])' "$row")"
    expected="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["checksum"])' "$row")"
    ctype="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["checksum_type"])' "$row")"
    if ! verify_data_checksum "$repo_root" "$href" "$expected" "$ctype"; then
      ok=0
      break
    fi
  done < <(python3 - "$repomd" <<'PY'
import json, sys
import xml.etree.ElementTree as ET
NS = "{http://linux.duke.edu/metadata/repo}"
root = ET.parse(sys.argv[1]).getroot()
for data in root.findall(f"{NS}data"):
    checksum = data.find(f"{NS}checksum")
    location = data.find(f"{NS}location")
    if checksum is None or location is None:
        continue
    print(json.dumps({
        "href": location.get("href"),
        "checksum": (checksum.text or "").strip(),
        "checksum_type": checksum.get("type", "sha"),
    }))
PY
)
  [[ "$ok" -eq 1 ]]
}
