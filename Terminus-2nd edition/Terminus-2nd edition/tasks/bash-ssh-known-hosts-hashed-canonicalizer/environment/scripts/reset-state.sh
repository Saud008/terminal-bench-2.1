#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
OUTPUT="${ROOT}/output"
STATE="${ROOT}/state"
mkdir -p "${OUTPUT}" "${STATE}"
: > "${OUTPUT}/normalized.hosts"
rm -f "${STATE}/kh-ledger.jsonl" "${STATE}/kh-manifest.json" "${STATE}/kh-ledger.jsonl.raw"
