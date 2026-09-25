#!/usr/bin/env bash
# Corpus manifest row helpers (hot path uses rf_read_manifest from common.sh).
set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../common.sh
source "${LIB}/common.sh"

rf_corpus_manifest_rows() {
  rf_read_manifest "$1"
}

