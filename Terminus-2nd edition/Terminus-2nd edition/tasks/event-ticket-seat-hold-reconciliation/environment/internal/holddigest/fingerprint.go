package stagewire

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "strings"

    "github.com/terminus/venuetixctl/internal/model"
)

func HoldSnapshotDigest(meta model.ScenarioMeta, sections []model.Section, holds []model.SeatHold) string {
    var parts []string
    for _, s := range sections {
        parts = append(parts, s.SectionID)
    }
    for _, h := range holds {
        parts = append(parts, fmt.Sprintf("%s:%s", h.HoldID, h.SeatID))
    }
    payload := strings.Join(parts, "|") + "|" + meta.CatalogSeed
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
