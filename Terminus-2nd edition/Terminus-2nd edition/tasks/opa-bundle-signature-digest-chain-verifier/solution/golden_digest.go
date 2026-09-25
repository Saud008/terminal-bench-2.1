package verify

import (
	"crypto/sha256"
	"encoding/hex"
	"sort"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MemberDigest(content []byte) string {
	h := sha256.Sum256(content)
	return hex.EncodeToString(h[:])
}

func ChainRoot(members []bundle.Member, _ []string) (string, map[string]string) {
	order := append([]bundle.Member(nil), members...)
	if ledger, err := bundle.LoadPreviewLedger(); err == nil && len(ledger.Order) > 0 {
		byCanon := make(map[string]bundle.Member, len(members))
		for _, m := range members {
			byCanon[m.Canonical] = m
		}
		order = order[:0]
		for _, canon := range ledger.Order {
			if m, ok := byCanon[canon]; ok {
				order = append(order, m)
			}
		}
	} else {
		sort.Slice(order, func(i, j int) bool {
			return order[i].Canonical < order[j].Canonical
		})
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
