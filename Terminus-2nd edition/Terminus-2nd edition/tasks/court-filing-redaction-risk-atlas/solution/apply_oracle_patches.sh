#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

cp "${ROOT_DIR}/files/aliasclosure_graph.go" /app/internal/nxtg01/alias.go
cp "${ROOT_DIR}/files/exhibitref_parser.go" /app/internal/nxtg02/link.go
cp "${ROOT_DIR}/files/sealgate_policy.go" /app/internal/nxtg03/terms.go
cp "${ROOT_DIR}/files/pageline_locator.go" /app/internal/nxtg04/locate.go
cp "${ROOT_DIR}/files/docket_primary.go" /app/internal/nxtg05/dedup.go
cp "${ROOT_DIR}/files/bundlevault_stage.go" /app/internal/nxtg06/bundle.go
cp "${ROOT_DIR}/files/atlas_emission.go" /app/internal/nxtg07/atlas.go

sed -i 's/rev\.IndexRevision = rev\.IndexRevision$/rev.IndexRevision = rev.IndexRevision + 1/' /app/internal/nxtg09/parties.go
sed -i 's/findings\[i\]\.FindingID > findings\[j\]\.FindingID/findings[i].FindingID < findings[j].FindingID/' /app/internal/nxtg10/risks.go
sed -i 's/return pages\[i\]\.PageNum > pages\[j\]\.PageNum/return pages[i].PageNum < pages[j].PageNum/' /app/internal/nxtg08/load.go

python3 <<'PY'
from pathlib import Path

path = Path("/app/internal/nxtg10/risks.go")
text = path.read_text(encoding="utf-8")
old = """func matchParty(text string, parties []model.Party, resolved map[string][]string) string {
    lower := strings.ToLower(text)
    for _, p := range parties {
        if strings.Contains(lower, strings.ToLower(p.Name)) {
            return p.ID
        }
        for _, alias := range resolved[p.ID] {
            if strings.Contains(lower, strings.ToLower(alias)) {
                return p.ID
            }
        }
    }
    return ""
}"""
new = """func matchParty(text string, parties []model.Party, resolved map[string][]string) string {
    lower := strings.ToLower(text)
    for _, p := range parties {
        if strings.Contains(lower, strings.ToLower(p.Name)) {
            return p.ID
        }
    }
    for _, p := range parties {
        for _, alias := range resolved[p.ID] {
            if strings.Contains(lower, strings.ToLower(alias)) {
                return p.ID
            }
        }
    }
    return ""
}"""
if old not in text:
    raise SystemExit("matchParty baseline block not found")
path.write_text(text.replace(old, new), encoding="utf-8")
PY

go vet -mod=readonly ./internal/...
