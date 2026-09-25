#!/usr/bin/env bash
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")/files" && pwd)"

install -m 0644 "$src/custody.py" /app/lib/musdoss/custody.py
install -m 0644 "$src/loans.py" /app/lib/musdoss/loans.py
install -m 0644 "$src/rights.py" /app/lib/musdoss/rights.py
install -m 0644 "$src/restoration.py" /app/lib/musdoss/restoration.py
install -m 0644 "$src/reconcile.py" /app/lib/musdoss/reconcile.py
install -m 0644 "$src/vault.py" /app/lib/musdoss/vault.py
install -m 0644 "$src/register.py" /app/lib/musdoss/register.py
install -m 0644 "$src/compose.py" /app/lib/musdoss/compose.py
install -m 0644 "$src/publish.py" /app/lib/musdoss/publish.py

bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh
test -x /usr/local/bin/musdoss
