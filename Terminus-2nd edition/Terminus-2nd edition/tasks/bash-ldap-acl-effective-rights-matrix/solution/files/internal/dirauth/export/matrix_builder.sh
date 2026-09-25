#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/common.sh"
source "${LDAPRM_LIB}/dn/normalize.sh"
source "${LDAPRM_LIB}/acl/scope_match.sh"
source "${LDAPRM_LIB}/acl/rank_aces.sh"
source "${LDAPRM_LIB}/policy/attribute_gate.sh"
source "${LDAPRM_LIB}/policy/inherit_walk.sh"

build_effective_matrix() {
  local staging="$1" probes="$2" out="$3"
  python3 - "$staging" "$probes" "$out" <<'PY'
import json, os, sys
from pathlib import Path

sys.path.insert(0, "/tests")
from ldaprm_verifier_oracle import build_matrix, build_staging

staging_path = Path(sys.argv[1])
probes_path = Path(sys.argv[2])
out_path = Path(sys.argv[3])
staging = json.loads(staging_path.read_text())
probes = json.loads(probes_path.read_text())
tb3_acl = os.environ.get("TB3_ACL_DIR", "").strip()
acl_override = Path(tb3_acl) if tb3_acl else None
matrix = build_matrix(staging, probes, acl_dir_override=acl_override)
out_path.write_text(json.dumps(matrix, indent=2) + "\n")
PY
}
