#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cp "${DIR}/patches/driver.sh" /app/lib/ebuild-phase/driver.sh
cp "${DIR}/patches/install.sh" /app/lib/ebuild-phase/install.sh
cp "${DIR}/patches/qa.sh" /app/lib/ebuild-phase/qa.sh
cp "${DIR}/patches/die.sh" /app/lib/ebuild-phase/die.sh
cp "${DIR}/patches/merge-ledger.sh" /app/lib/ebuild-phase/merge-ledger.sh
chmod +x /app/lib/ebuild-phase/*.sh /app/bin/ebuild-phase
