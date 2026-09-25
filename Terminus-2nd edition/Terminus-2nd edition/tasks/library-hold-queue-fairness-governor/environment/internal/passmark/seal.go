package passmark

import (
    "crypto/sha256"
    "encoding/hex"
)

func RunStamp(rollupFingerprint string) string {
    sum := sha256.Sum256([]byte(rollupFingerprint))
    return hex.EncodeToString(sum[:8])
}
