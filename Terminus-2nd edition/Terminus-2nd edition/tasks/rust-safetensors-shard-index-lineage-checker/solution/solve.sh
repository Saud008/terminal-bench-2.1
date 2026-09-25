# Oracle solve — task identity rust-safetensors-shard-index-lineage-checker token f4e8b203
#!/bin/bash
set -euo pipefail
ENV="/app/environment"
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"

require_file() {
  local candidate="$1"
  if [[ ! -f "$candidate" ]]; then
    echo "oracle missing patch file: $candidate" >&2
    exit 1
  fi
}

ensure_state_dirs() {
  mkdir -p /app/var /app/lineage
  rm -f /app/var/xr7_journal.ndjson /app/lineage/weight_lineage_atlas.json
}

ensure_state_dirs

for f in wx_span_gate wx_width_table wx_digest_seal wx_parent_bind wx_roll_journal wx_finalize_report; do
  require_file "$ROOT_DIR/files/${f}.rs"
done

install -D -m 0644 "$ROOT_DIR/files/wx_span_gate.rs" "$ENV/src/wx_span_gate.rs"
install -D -m 0644 "$ROOT_DIR/files/wx_width_table.rs" "$ENV/src/wx_width_table.rs"
install -D -m 0644 "$ROOT_DIR/files/wx_digest_seal.rs" "$ENV/src/wx_digest_seal.rs"
install -D -m 0644 "$ROOT_DIR/files/wx_parent_bind.rs" "$ENV/src/wx_parent_bind.rs"
patch -p0 "$ENV/src/wx_roll_journal.rs" < "$ROOT_DIR/files/wx_roll_journal.patch"
install -D -m 0644 "$ROOT_DIR/files/wx_finalize_report.rs" "$ENV/src/wx_finalize_report.rs"

cd /app/environment
CARGO_TARGET_DIR=/app/environment/target
rm -rf target
cargo build --release
install -m 0755 target/release/xr7 /app/bin/xr7

CATALOGS="${XR7_CATALOG_ROOT:-/app/environment/registry/catalogs}"
WEIGHTS="${XR7_WEIGHT_ROOT:-/app/environment/registry/weights}"
JOURNAL="/app/var/xr7_journal.ndjson"
ATLAS="/app/lineage/weight_lineage_atlas.json"
/app/bin/xr7 catalog-scan --catalog-dir "$CATALOGS" --weight-root "$WEIGHTS" --journal "$JOURNAL"
/app/bin/xr7 atlas-publish --journal "$JOURNAL" --catalog-dir "$CATALOGS" --weight-root "$WEIGHTS" --atlas "$ATLAS"
if [[ ! -s "$JOURNAL" ]]; then
  echo "journal empty after catalog-scan" >&2
  exit 1
fi
if [[ ! -s "$ATLAS" ]]; then
  echo "lineage atlas empty after atlas-publish" >&2
  exit 1
fi
