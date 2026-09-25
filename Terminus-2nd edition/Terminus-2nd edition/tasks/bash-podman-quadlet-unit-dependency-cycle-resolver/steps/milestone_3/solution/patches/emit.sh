#!/usr/bin/env bash
# Render systemd unit files from parsed quadlets (fixed).

set -euo pipefail

source /app/lib/common.sh
source /app/lib/dag.sh

run_render() {
  local tree="$1"
  local outdir="$2"
  local tmp_parse tmp_order
  tmp_parse="$(mktemp)"
  tmp_order="$(mktemp)"
  if ! run_order "${tree}" "${tmp_order}"; then
    rm -f "${tmp_parse}" "${tmp_order}"
    return 2
  fi
  run_parse "${tree}" "${tmp_parse}"
  mkdir -p "${outdir}"
  python3 - "${tmp_parse}" "${tmp_order}" "${outdir}" <<'PY'
import json, sys
from pathlib import Path

parse_data = json.loads(Path(sys.argv[1]).read_text())
order = json.loads(Path(sys.argv[2]).read_text())["order"]
outdir = Path(sys.argv[3])
units = parse_data["units"]

for name in order:
    meta = units[name]
    unit = meta.get("unit", {})
    svc = meta.get("service", {})
    ctr = meta.get("container", {})
    lines = ["[Unit]"]
    desc = unit.get("Description", name)
    lines.append(f"Description={desc}")
    for key in ("After", "Wants", "Requires"):
        vals = unit.get(key, [])
        if vals:
            lines.append(f"{key}={' '.join(vals)}")
    lines.append("")
    lines.append("[Service]")
    envs = svc.get("EnvironmentFile", [])
    for env in envs:
        lines.append(f"EnvironmentFile={env}")
    restart = svc.get("Restart", "no")
    lines.append(f"Restart={restart}")
    image = ctr.get("Image", "localhost/missing:latest")
    base = name.replace(".service", "")
    lines.append(f"ExecStart=/usr/bin/podman run --name {base} {image}")
    lines.append("")
    lines.append("[Install]")
    lines.append("WantedBy=multi-user.target")
    (outdir / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
  rm -f "${tmp_parse}" "${tmp_order}"
  return 0
}
