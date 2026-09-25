#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
STATE="${ROOT}/state"
OUTPUT="${ROOT}/output"
mkdir -p "${OUTPUT}" "${STATE}"
: > "${OUTPUT}/plan.json"
rm -f "${STATE}/parsed-manifest.tsv" "${STATE}/staging-meta.json" "${STATE}/run-seq.json"
