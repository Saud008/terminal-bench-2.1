#!/usr/bin/env bash
# Oracle solve — task identity rust-pep440-wheel-resolution-explainer token 440pep02
set -euo pipefail
APP=/app
ENV="${APP}/environment"
PATCHES="${APP}/solution/patches"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${ENV}"
patch -p1 --forward < "${ROOT_DIR}/patches/m01.rs.patch"
patch -p1 --forward < "${ROOT_DIR}/patches/m02.rs.patch"
patch -p1 --forward < "${ROOT_DIR}/patches/m03.rs.patch"
patch -p1 --forward < "${ROOT_DIR}/patches/m04.rs.patch"
patch -p1 --forward < "${ROOT_DIR}/patches/m05.rs.patch"
patch -p1 --forward < "${ROOT_DIR}/patches/m06.rs.patch"
patch -p1 --forward < "${ROOT_DIR}/patches/m07.rs.patch"

CARGO_TARGET_DIR=/app/environment/target cargo build --release --locked
install -m 0755 target/release/whres /app/bin/whres

bash /app/scripts/reset-state.sh
/app/bin/whres load --scenario httpx-pin-requests --run-id oracle-seal
/app/bin/whres analyze --run-id oracle-seal
mkdir -p /app/output
/app/bin/whres emit --run-id oracle-seal --output /app/output/oracle-seal.json
test -s /app/output/oracle-seal.json
echo "rust-pep440-wheel-resolution-explainer oracle ready"
