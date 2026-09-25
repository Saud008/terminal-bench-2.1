#!/usr/bin/env bash
# Oracle solve — task identity go-oci-layer-whiteout-filesystem-materializer token 9946c9ca
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p2 < patches/layerfuse-oracle.patch

export PATH="/usr/local/go/bin:${PATH}"
cd /app
go build -mod=readonly -o /usr/local/bin/layerfuse ./cmd/layerfuse
