#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=aliases.sh
source "$(dirname "${BASH_SOURCE[0]}")/aliases.sh"

load_bundle_rules() {
  local root="$1"
  local alias_json manifest
  alias_json="$(load_alias_map "$root")"
  manifest="$(read_manifest "$root")"
  HOSTSCTL_LIB="${HOSTSCTL_LIB}" python3 - "$root" "$manifest" "$alias_json" <<'PY'
import json
import os
import pathlib
import subprocess
import sys

root, manifest, alias_json = sys.argv[1:4]
manifest = json.loads(manifest)
lib = os.environ["HOSTSCTL_LIB"]


def expand_daemons(csv: str) -> list[str]:
    proc = subprocess.run(
        [
            "bash",
            "-c",
            'source "${HOSTSCTL_LIB}/common.sh"; '
            'source "${HOSTSCTL_LIB}/aliases.sh"; '
            'expand_rule_daemons "$1" "$2"',
            "_",
            alias_json,
            csv,
        ],
        env={**os.environ, "HOSTSCTL_LIB": lib},
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def split_clients(part: str) -> list[str]:
    part = part.strip()
    if part.upper().startswith("ALL EXCEPT"):
        rest = part[len("ALL EXCEPT") :].strip()
        subs = rest.split() if rest else []
        return ["ALL EXCEPT " + " ".join(subs)]
    return [p.strip() for p in part.split(",") if p.strip()]


def parse_file(side: str, rel: str) -> list[dict]:
    path = os.path.join(root, rel)
    text = pathlib.Path(path).read_text(encoding="utf-8")
    out: list[dict] = []
    buf = ""
    line_no = 0
    for raw_line in text.splitlines():
        line_no += 1
        chunk = raw_line.rstrip("\n")
        if chunk.endswith("\\"):
            buf += chunk[:-1] + " "
            continue
        buf += chunk
        line = buf.strip()
        buf = ""
        if not line or line.startswith("#") or ":" not in line:
            continue
        left, right = line.split(":", 1)
        daemons = expand_daemons(left)
        out.append(
            {
                "side": side,
                "origin": rel,
                "line": line_no,
                "daemons": daemons,
                "clients": split_clients(right),
            }
        )
    return out


rules: list[dict] = []
for rel in manifest.get("allow_files", []):
    rules.extend(parse_file("allow", rel))
for rel in manifest.get("deny_files", []):
    rules.extend(parse_file("deny", rel))
print(json.dumps(rules))
PY
}
