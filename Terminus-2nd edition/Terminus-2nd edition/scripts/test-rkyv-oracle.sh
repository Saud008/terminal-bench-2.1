#!/usr/bin/env bash
set -euxo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TASK="${REPO}/tasks/rkyv-archived-relative-pointer-relocation-repair"
WORKDIR="/tmp/rkyv-oracle-test"
rm -rf "${WORKDIR}"
cp -a "${TASK}/environment/." "${WORKDIR}/"
export APP_ROOT="${WORKDIR}"
export PATH="${HOME}/.cargo/bin:${PATH}"

bash "${TASK}/solution/solve.sh" || {
  # solve.sh may fail on install outside Docker; use local target binaries
  export PATH="${WORKDIR}/target/debug:${PATH}"
  bash "${APP_ROOT}/scripts/reset-state.sh"
  for name in baseline nested-vec wide-enum pool-dup nested-dedupe; do
    archv reloc \
      --input "${APP_ROOT}/fixtures/archives/${name}.rkyv" \
      --output "${APP_ROOT}/output/${name}-reloc.rkyv" \
      --dedupe
    archv validate --input "${APP_ROOT}/output/${name}-reloc.rkyv"
    archv deserialize \
      --input "${APP_ROOT}/output/${name}-reloc.rkyv" \
      --output "${APP_ROOT}/output/${name}.json"
  done
}

echo "=== smoke outputs ==="
ls -la "${WORKDIR}/output/"
