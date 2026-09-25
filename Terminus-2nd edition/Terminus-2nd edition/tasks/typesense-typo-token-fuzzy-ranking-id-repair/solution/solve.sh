#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/golden_search_stage.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "golden_search_stage.rs not found" >&2; exit 1; }

cp -f "${SOL_DIR}/golden_token_dedupe.rs" /app/crates/ts-tokenize/src/token_dedupe.rs
cp -f "${SOL_DIR}/golden_prefix_score.rs" /app/crates/ts-fuzzy/src/prefix_score.rs
cp -f "${SOL_DIR}/golden_tiebreak.rs" /app/crates/ts-ranker/src/tiebreak.rs
cp -f "${SOL_DIR}/golden_counter.rs" /app/crates/ts-facet/src/counter.rs
cp -f "${SOL_DIR}/golden_search_stage.rs" /app/crates/search-export/src/search_stage.rs
cp -f "${SOL_DIR}/golden_store.rs" /app/crates/ingest-stage/src/store.rs
sed -i 's/\r$//' /app/crates/ts-tokenize/src/token_dedupe.rs \
  /app/crates/ts-fuzzy/src/prefix_score.rs \
  /app/crates/ts-ranker/src/tiebreak.rs \
  /app/crates/ts-facet/src/counter.rs \
  /app/crates/search-export/src/search_stage.rs \
  /app/crates/ingest-stage/src/store.rs

cargo build --release --locked -p typesense-search-cli
install -m 0755 /app/target/release/typesense-search-cli /usr/local/bin/typesense-search-cli
bash /app/scripts/reset-state.sh
