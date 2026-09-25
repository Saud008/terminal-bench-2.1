package idemstamp

import (
    "crypto/sha256"
    "encoding/hex"
)

func RunStamp(snapshotDigest string) string {
    sum := sha256.Sum256([]byte(snapshotDigest))
    return hex.EncodeToString(sum[:8])
}
