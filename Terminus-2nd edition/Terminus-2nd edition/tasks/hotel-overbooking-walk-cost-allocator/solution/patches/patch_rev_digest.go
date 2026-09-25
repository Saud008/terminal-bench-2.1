package revsnap

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "sort"
    "strings"

    "github.com/terminus/overbookctl/internal/model"
)

func CapacityFingerprint(meta model.ScenarioMeta, rooms []model.Room, maintenance []model.Maintenance) string {
    roomParts := make([]string, 0, len(rooms))
    for _, r := range rooms {
        roomParts = append(roomParts, fmt.Sprintf("%s:%s", r.RoomID, r.RoomTypeID))
    }
    sort.Strings(roomParts)
    maintParts := make([]string, 0, len(maintenance))
    for _, m := range maintenance {
        maintParts = append(maintParts, fmt.Sprintf("%s:%s:%s", m.RoomID, m.StartDate, m.EndDate))
    }
    sort.Strings(maintParts)
    payload := strings.Join(roomParts, "|") + "|" + meta.CatalogSeed + "|" + strings.Join(maintParts, "|")
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
