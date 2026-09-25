#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
OUTPUT="${ROOT}/output"
STATE="${ROOT}/state"
mkdir -p "${OUTPUT}" "${STATE}"
: > "${OUTPUT}/initramfs.manifest"
rm -f "${STATE}/irfs-ledger.jsonl" "${STATE}/irfs-manifest.json"
