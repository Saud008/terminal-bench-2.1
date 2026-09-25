package registrylock

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "strings"

    "github.com/terminus/intakectl/internal/sheltertypes"
)

func RegistryDigest(meta sheltertypes.ScenarioMeta, kennels []sheltertypes.Kennel, quarantine []sheltertypes.QuarantineWindow) string {
    var parts []string
    for _, k := range kennels {
        parts = append(parts, fmt.Sprintf("%s:%s", k.KennelID, k.SpeciesCode))
    }
    payload := strings.Join(parts, "|") + "|" + meta.CatalogSeed
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
