#!/usr/bin/env bash
# SPDX token normalizer used by catalog previews only.
set -euo pipefail
tr '[:lower:]' '[:upper:]' <<< "${1:-}"
