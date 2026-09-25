package verify

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/terminus/bundlectl/internal/bundle"
)

// LegacyChainRoot computes a rolling digest using manifest declaration order.
// Deprecated diagnostic helper — contract acceptance uses lexicographic preview order.
func LegacyChainRoot(members []bundle.Member, manifestOrder []string) (string, map[string]string) {
	order := make([]bundle.Member, 0, len(members))
	byRaw := make(map[string]bundle.Member, len(members))
	for _, m := range members {
		byRaw[m.Raw] = m
	}
	for _, raw := range manifestOrder {
		if m, ok := byRaw[raw]; ok {
			order = append(order, m)
		}
	}
	digests := make(map[string]string, len(order))
	state := sha256.Sum256(nil)
	for _, m := range order {
		fd := sha256.Sum256(m.Bytes)
		digests[m.Canonical] = hex.EncodeToString(fd[:])
		h := sha256.New()
		h.Write(state[:])
		h.Write([]byte(m.Canonical))
		h.Write(fd[:])
		copy(state[:], h.Sum(nil))
	}
	return hex.EncodeToString(state[:]), digests
}
