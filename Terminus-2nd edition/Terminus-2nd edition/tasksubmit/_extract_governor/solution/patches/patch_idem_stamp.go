package passmark

import (
    "crypto/sha256"
    "encoding/hex"
)

func RunStamp(scenario, rollupFingerprint string) string {
    sum := sha256.Sum256([]byte(rollupFingerprint + "|" + scenario))
    return hex.EncodeToString(sum[:8])
}
