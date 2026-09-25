#!/usr/bin/env bash
# Pack all Harbor upload zips — delegates to pack_zip.sh --all
set -euo pipefail
exec "$(cd "$(dirname "$0")" && pwd)/pack_zip.sh" --all
