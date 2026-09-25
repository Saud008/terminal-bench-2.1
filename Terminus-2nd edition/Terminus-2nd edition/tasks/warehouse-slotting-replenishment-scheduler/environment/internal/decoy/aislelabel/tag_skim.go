package aislelabel

import "github.com/terminus/whslot/internal/whmodel"

// Decoy — aisle label preview only; not on replen hot path.
func PreviewLabels(skus []whmodel.SKU) []string {
	out := make([]string, 0, len(skus))
	for _, s := range skus {
		out = append(out, s.SKUID+"@"+s.PickFaceSlot)
	}
	return out
}
