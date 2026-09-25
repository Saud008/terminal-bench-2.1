package verify

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MemberDigest(content []byte) string {
	h := sha256.Sum256(content)
	return hex.EncodeToString(h[:])
}

// ChainRoot uses manifest declaration order (broken — must follow preview ledger lex order).
func ChainRoot(members []bundle.Member, manifestOrder []string) (string, map[string]string) {
	order := make([]bundle.Member, 0, len(members))
	byRaw := make(map[string]bundle.Member, len(members))
	for _, m := range members {
		byRaw[m.Raw] = m
	}
	if len(manifestOrder) > 0 {
		for _, raw := range manifestOrder {
			if m, ok := byRaw[raw]; ok {
				order = append(order, m)
			}
		}
	} else {
		order = append(order, members...)
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

func SortedChainRoot(members []bundle.Member) (string, map[string]string) {
	return ChainRoot(members, nil)
}
