package stagewire

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "sort"
    "strings"

    "github.com/terminus/venuetixctl/internal/model"
)

func HoldSnapshotDigest(meta model.ScenarioMeta, sections []model.Section, holds []model.SeatHold) string {
    ids := make([]string, 0, len(sections))
    for _, s := range sections {
        ids = append(ids, s.SectionID)
    }
    sort.Strings(ids)
    var parts []string
    parts = append(parts, ids...)
    for _, h := range holds {
        parts = append(parts, fmt.Sprintf("%s:%s", h.HoldID, h.SeatID))
    }
    payload := strings.Join(parts, "|") + "|" + meta.CatalogSeed
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
