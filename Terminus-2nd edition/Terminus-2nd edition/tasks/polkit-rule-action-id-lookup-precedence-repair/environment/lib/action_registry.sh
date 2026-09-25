#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pk_lookup_action() {
  local action_id="$1"
  local actions_root
  actions_root="$(actions_dir)"
  python3 - "$actions_root" "$action_id" <<'PY'
import json, sys, xml.etree.ElementTree as ET
from pathlib import Path

root = Path(sys.argv[1])
action_id = sys.argv[2]
xml_path = root / f"{action_id}.xml"
js_path = root / f"{action_id}.js"

def load_xml():
    if not xml_path.is_file():
        return None
    elem = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    return {
        "format": "xml",
        "allow_active": elem.findtext("allow_active", "no"),
        "allow_inactive": elem.findtext("allow_inactive", "no"),
    }

def load_js():
    if not js_path.is_file():
        return None
    data = json.loads(js_path.read_text(encoding="utf-8"))
    return {
        "format": "js",
        "allow_active": data["allow_active"],
        "allow_inactive": data["allow_inactive"],
    }

row = load_xml() or load_js()
print(json.dumps(row if row else {}))
PY
}
