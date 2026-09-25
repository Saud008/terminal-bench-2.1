#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
OUTPUT="${ROOT}/output"
mkdir -p "${OUTPUT}"
: > "${OUTPUT}/resolve.json"

# Restore fixture symlink used by prefix resolution fixtures.
ACTIVE="${ROOT}/prefixes/active/stellaris"
CANON="${ROOT}/prefixes/canonical/stellaris"
mkdir -p "${CANON}"
rm -f "${ACTIVE}"
ln -sfn "../canonical/stellaris" "${ACTIVE}"
