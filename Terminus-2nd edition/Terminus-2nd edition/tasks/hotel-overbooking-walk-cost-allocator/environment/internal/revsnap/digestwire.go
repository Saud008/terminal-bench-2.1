package revsnap

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "strings"

    "github.com/terminus/overbookctl/internal/model"
)

func CapacityFingerprint(meta model.ScenarioMeta, rooms []model.Room, maintenance []model.Maintenance) string {
    var parts []string
    for _, r := range rooms {
        parts = append(parts, fmt.Sprintf("%s:%s", r.RoomID, r.RoomTypeID))
    }
    payload := strings.Join(parts, "|") + "|" + meta.CatalogSeed
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
