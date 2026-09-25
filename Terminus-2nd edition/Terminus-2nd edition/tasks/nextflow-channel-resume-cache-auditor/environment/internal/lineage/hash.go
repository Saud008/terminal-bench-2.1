package lineage

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"
)

// ComputeLineageDigest folds parent hashes then task hash root-first.
func ComputeLineageDigest(parents []string, taskHash string) string {
	parts := []string{taskHash}
	parts = append(parts, parents...)
	h := sha256.New()
	for _, p := range parts {
		h.Write([]byte(strings.TrimSpace(p)))
		h.Write([]byte{0})
	}
	return hex.EncodeToString(h.Sum(nil))
}
