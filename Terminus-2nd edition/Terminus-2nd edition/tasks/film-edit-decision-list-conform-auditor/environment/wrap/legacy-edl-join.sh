#!/usr/bin/env bash
# Legacy EDL join helper — outside conform stage/publish hot path.
set -euo pipefail
cat "$1" "$2"
