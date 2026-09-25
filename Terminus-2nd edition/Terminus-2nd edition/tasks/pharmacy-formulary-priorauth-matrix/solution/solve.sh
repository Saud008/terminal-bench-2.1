# Oracle solve — task identity pharmacy-formulary-priorauth-matrix token 7cae68b0
#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/install_oracle_patches.sh"

python3 /app/fixtures/build_fixtures.py
FORMULATRIX_HIDDEN_ROOT=/opt/verifier-fixtures/formulatrix python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/formulatrix ./cmd/formulatrix
test -x /app/bin/formulatrix
echo "pharmacy-formulary-priorauth-matrix oracle ready"
