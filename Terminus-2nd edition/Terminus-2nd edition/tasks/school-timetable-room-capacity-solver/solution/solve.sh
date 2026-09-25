# Oracle solve — task identity school-timetable-room-capacity-solver token 6c5f5bba
#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

bash "${ROOT_DIR}/oracle_apply.sh"
python3 /app/fixtures/gen_timetable_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/ttalloc ./cmd/ttalloc
chmod +x /app/bin/ttalloc
test -x /app/bin/ttalloc
echo "school-timetable-room-capacity-solver oracle ready"
