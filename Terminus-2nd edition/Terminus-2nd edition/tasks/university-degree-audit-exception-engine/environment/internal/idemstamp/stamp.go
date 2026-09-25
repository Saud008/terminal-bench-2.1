package idemstamp

import (
    "crypto/sha256"
    "encoding/hex"
)

func RunStamp(scenario, materialFingerprint string) string {
    sum := sha256.Sum256([]byte(materialFingerprint + scenario))
    return hex.EncodeToString(sum[:8])
}
