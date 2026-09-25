package snaprollup

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "sort"
    "strings"

    "github.com/terminus/holdfairctl/internal/model"
)

func RollupFingerprint(meta model.ScenarioMeta, patrons []model.Patron, holds []model.HoldRequest) string {
    ids := make([]string, 0, len(patrons))
    seen := map[string]struct{}{}
    for _, p := range patrons {
        if _, ok := seen[p.PatronID]; ok {
            continue
        }
        seen[p.PatronID] = struct{}{}
        ids = append(ids, p.PatronID)
    }
    sort.Strings(ids)
    var parts []string
    parts = append(parts, ids...)
    for _, h := range holds {
        parts = append(parts, fmt.Sprintf("%s:%s", h.RequestID, h.ItemID))
    }
    payload := strings.Join(parts, "|") + "|" + meta.CatalogSeed
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
