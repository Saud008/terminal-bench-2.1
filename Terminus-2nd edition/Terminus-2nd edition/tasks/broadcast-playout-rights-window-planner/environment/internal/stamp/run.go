package stamp

import (
    "crypto/sha256"
    "encoding/hex"
)

func ForScenario(scenario, runwayDigest string) string {
    h := sha256.Sum256([]byte(runwayDigest + "|" + scenario))
    return hex.EncodeToString(h[:8])
}
