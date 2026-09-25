# Oracle solve — task identity rust-onnx-tensor-shape-propagation-auditor token a7c3e901
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
  mkdir -p /app/state /app/output
  rm -f /app/state/tensor_prop_batch.jsonl /app/output/constraint_diagnostic_report.json
}

ensure_state_dirs

for f in dim_symbol broadcast_rules init_bind input_defaults op_infer staging_store audit_export; do
  require_file "$ROOT_DIR/files/tg_${f}.rs"
done

install -D -m 0644 "$ROOT_DIR/files/tg_dim_symbol.rs" "$ENV/vlx_core/c02_sym/src/slot_alpha.rs"
install -D -m 0644 "$ROOT_DIR/files/tg_broadcast_rules.rs" "$ENV/vlx_core/c03_align/src/slot_beta.rs"
install -D -m 0644 "$ROOT_DIR/files/tg_init_bind.rs" "$ENV/vlx_core/c04_bind/src/slot_gamma.rs"
install -D -m 0644 "$ROOT_DIR/files/tg_input_defaults.rs" "$ENV/vlx_core/c05_port/src/slot_delta.rs"
install -D -m 0644 "$ROOT_DIR/files/tg_op_infer.rs" "$ENV/vlx_core/c06_node/src/slot_epsilon.rs"
install -D -m 0644 "$ROOT_DIR/files/tg_staging_store.rs" "$ENV/vlx_core/c08_store/src/slot_eta.rs"
install -D -m 0644 "$ROOT_DIR/files/tg_audit_export.rs" "$ENV/vlx_core/c09_emit/src/slot_theta.rs"

cd /app/environment
export CARGO_TARGET_DIR=/app/environment/target
rm -rf target
cargo build --release -p shapeprop
install -m 0755 target/release/shapeprop /app/environment/tools/shapeprop/shapeprop

GRAPHS="${TB3_GRAPH_DIR:-/app/environment/fixtures/graphs}"
LEDGER="/app/state/tensor_prop_batch.jsonl"
REPORT="/app/output/constraint_diagnostic_report.json"
/app/environment/tools/shapeprop/shapeprop batch-propagate --graph-batch "$GRAPHS" --ledger "$LEDGER"
/app/environment/tools/shapeprop/shapeprop emit-violations --ledger "$LEDGER" --graph-batch "$GRAPHS" --report "$REPORT"
if [[ ! -s "$LEDGER" ]]; then
  echo "ledger empty after batch-propagate" >&2
  exit 1
fi
if [[ ! -s "$REPORT" ]]; then
  echo "diagnostic report empty after emit-violations" >&2
  exit 1
fi
