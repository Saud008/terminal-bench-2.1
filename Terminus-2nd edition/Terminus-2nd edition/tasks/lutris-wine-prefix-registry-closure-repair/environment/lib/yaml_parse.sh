#!/usr/bin/env bash
# Parse registry.yml into tab-separated records for Bash consumers.

yaml_parse_registry() {
  local registry_file="$1"
  python3 - "$registry_file" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = text.splitlines()

entries: list[dict] = []
current: dict | None = None
section: str | None = None
provides_key: str | None = None

def flush() -> None:
    global current
    if current is not None:
        entries.append(current)
        current = None

for raw in lines:
    line = raw.split("#", 1)[0].rstrip()
    if not line.strip():
        continue
    if re.match(r"^entries:\s*$", line):
        continue
    m_item = re.match(r"^\s*-\s+slug:\s*(.+)$", line)
    if m_item:
        flush()
        slug = m_item.group(1).strip().strip('"').strip("'")
        current = {
            "slug": slug,
            "runner": "",
            "prefix": "",
            "dxvk_pin": "",
            "requires": [],
            "provides": {},
        }
        section = None
        provides_key = None
        continue
    if current is None:
        continue
    m_runner = re.match(r"^\s+runner:\s*(.+)$", line)
    if m_runner:
        val = m_runner.group(1).strip()
        if val in ("null", "~", ""):
            current["runner"] = ""
        else:
            current["runner"] = val.strip('"').strip("'")
        continue
    m_prefix = re.match(r"^\s+prefix:\s*(.+)$", line)
    if m_prefix:
        current["prefix"] = m_prefix.group(1).strip().strip('"').strip("'")
        continue
    m_pin = re.match(r"^\s+dxvk_pin:\s*(.+)$", line)
    if m_pin:
        current["dxvk_pin"] = m_pin.group(1).strip().strip('"').strip("'")
        continue
    m_requires = re.match(r"^\s+requires:\s*$", line)
    if m_requires:
        section = "requires"
        continue
    m_provides = re.match(r"^\s+provides:\s*$", line)
    if m_provides:
        section = "provides"
        provides_key = None
        continue
    m_req_item = re.match(r"^\s+-\s+(.+)$", line)
    if m_req_item and section == "requires":
        dep = m_req_item.group(1).strip().strip('"').strip("'")
        current["requires"].append(dep)
        continue
    m_provide = re.match(r"^\s+([a-zA-Z0-9_]+):\s*(.+)$", line)
    if m_provide and section == "provides":
        key = m_provide.group(1)
        val = m_provide.group(2).strip().strip('"').strip("'")
        current["provides"][key] = val
        continue

flush()

for entry in entries:
    slug = entry["slug"]
    print(f"ENTRY|{slug}|{entry['runner']}|{entry['prefix']}|{entry['dxvk_pin']}")
    for dep in entry["requires"]:
        print(f"REQUIRES|{slug}|{dep}")
    for key, val in sorted(entry["provides"].items()):
        print(f"PROVIDES|{slug}|{key}|{val}")
PY
}
