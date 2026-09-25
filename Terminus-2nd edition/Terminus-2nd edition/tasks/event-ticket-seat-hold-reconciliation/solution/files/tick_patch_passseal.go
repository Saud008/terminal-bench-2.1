package idemstamp

import (
    "crypto/sha256"
    "encoding/hex"
)

func RunStamp(scenario, snapshotDigest string) string {
    sum := sha256.Sum256([]byte(snapshotDigest + "|" + scenario))
    return hex.EncodeToString(sum[:8])
}
