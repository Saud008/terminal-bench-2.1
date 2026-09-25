#!/usr/bin/env bash
set -euo pipefail
# Verifier rebuild hook — refresh bash module permissions before pytest.
find /app/lib -type f -name '*.sh' -print0 | xargs -0 chmod +x
find /app/bin -type f -print0 | xargs -0 chmod +x 2>/dev/null || true
: > /app/output/.attest-rebuild-touch
