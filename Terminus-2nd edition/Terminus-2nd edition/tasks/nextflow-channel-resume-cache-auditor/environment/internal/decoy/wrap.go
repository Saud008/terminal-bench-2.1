package decoy

import (
	"crypto/sha256"
	"encoding/hex"
	"sort"
)

// MergeCacheKeys is a diagnostic helper not used by ingest or export.
func MergeCacheKeys(keys []string) string {
	cp := append([]string(nil), keys...)
	sort.Strings(cp)
	h := sha256.New()
	for _, k := range cp {
		h.Write([]byte(k))
	}
	return hex.EncodeToString(h.Sum(nil))
}
