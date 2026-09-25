package lineage

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"
)

func ComputeLineageDigest(parents []string, taskHash string) string {
	parts := append(append([]string{}, parents...), taskHash)
	h := sha256.New()
	for _, p := range parts {
		h.Write([]byte(strings.TrimSpace(p)))
		h.Write([]byte{0})
	}
	return hex.EncodeToString(h.Sum(nil))
}
