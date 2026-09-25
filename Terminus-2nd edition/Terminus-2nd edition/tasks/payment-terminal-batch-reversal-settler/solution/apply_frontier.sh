#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

require_oracle_file() {
  local path="$1"
  if [ ! -f "${path}" ]; then
    echo "oracle bundle missing: ${path}" >&2
    exit 1
  fi
}

assert_non_empty_target() {
  local path="$1"
  if [ ! -s "${path}" ]; then
    echo "oracle install produced empty target: ${path}" >&2
    exit 1
  fi
}

normalize_go_tree() {
  find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
}

normalize_go_tree

require_oracle_file "${FILES_DIR}/oracle_txnstate.go"
sed -i 's/strings.ToUpper(code)/strings.ToLower(code)/' /app/internal/txnstate/state.go
assert_non_empty_target /app/internal/txnstate/state.go

require_oracle_file "${FILES_DIR}/oracle_reversal.go"
cp "${FILES_DIR}/oracle_reversal.go" /app/internal/reversal/pair.go
assert_non_empty_target /app/internal/reversal/pair.go

require_oracle_file "${FILES_DIR}/oracle_cutoff.go"
cp "${FILES_DIR}/oracle_cutoff.go" /app/internal/cutoff/window.go
assert_non_empty_target /app/internal/cutoff/window.go

require_oracle_file "${FILES_DIR}/oracle_seqguard.go"
cp "${FILES_DIR}/oracle_seqguard.go" /app/internal/seqguard/guard.go
assert_non_empty_target /app/internal/seqguard/guard.go

require_oracle_file "${FILES_DIR}/oracle_journal.go"
cp "${FILES_DIR}/oracle_journal.go" /app/internal/journal/compile.go
assert_non_empty_target /app/internal/journal/compile.go

require_oracle_file "${FILES_DIR}/oracle_seal.go"
sed -i 's/WitnessHMAC(scenario.TerminalKeyHex, string(raw))/WitnessHMAC(scenario.TerminalKeyHex, jDigest)/' /app/internal/seal/bundle.go
assert_non_empty_target /app/internal/seal/bundle.go

require_oracle_file "${FILES_DIR}/oracle_settlepromote.go"
cp "${FILES_DIR}/oracle_settlepromote.go" /app/internal/settlepromote/finalize.go
assert_non_empty_target /app/internal/settlepromote/finalize.go

echo "payment-terminal-batch-reversal-settler oracle patches installed"
