package sarif

import (
	"crypto/sha256"
	"encoding/hex"
)

func SHA256Bytes(raw []byte) string {
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}
