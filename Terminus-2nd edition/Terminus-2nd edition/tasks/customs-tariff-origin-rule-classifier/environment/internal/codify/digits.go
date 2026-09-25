package codify

import "strings"

// NormalizeHS pads harmonized codes to HS10 per hs-normalize-contract.md.
func NormalizeHS(raw string) string {
	cleaned := strings.NewReplacer(".", "", "-", "", " ", "").Replace(raw)
	if len(cleaned) > 10 {
		cleaned = cleaned[:10]
	}
	for len(cleaned) < 8 {
		cleaned = cleaned + "0"
	}
	return cleaned
}
