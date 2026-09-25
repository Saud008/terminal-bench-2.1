#!/usr/bin/env bash
# Oracle solve — task identity dnsmasq-lease-authoritative-renewal-skew-ledger token da1915b9
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

python3 "${ROOT}/apply_oracle.py"

cd /app
/usr/local/go/bin/go build -mod=readonly -o /usr/local/bin/dnsmasqledger ./cmd/dnsmasqledger
bash /app/scripts/reset-state.sh
echo "dnsmasqledger oracle ready"
