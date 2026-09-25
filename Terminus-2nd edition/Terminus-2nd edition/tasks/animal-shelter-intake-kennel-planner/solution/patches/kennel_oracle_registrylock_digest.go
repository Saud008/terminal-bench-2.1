package registrylock

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "sort"
    "strings"

    "github.com/terminus/intakectl/internal/sheltertypes"
)

func RegistryDigest(meta sheltertypes.ScenarioMeta, kennels []sheltertypes.Kennel, quarantine []sheltertypes.QuarantineWindow) string {
    kennelParts := make([]string, 0, len(kennels))
    for _, k := range kennels {
        kennelParts = append(kennelParts, fmt.Sprintf("%s:%s", k.KennelID, k.SpeciesCode))
    }
    sort.Strings(kennelParts)
    quarParts := make([]string, 0, len(quarantine))
    for _, q := range quarantine {
        quarParts = append(quarParts, fmt.Sprintf("%s:%s:%s", q.KennelID, q.StartDate, q.EndDate))
    }
    sort.Strings(quarParts)
    payload := strings.Join(kennelParts, "|") + "|" + meta.CatalogSeed + "|" + strings.Join(quarParts, "|")
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
