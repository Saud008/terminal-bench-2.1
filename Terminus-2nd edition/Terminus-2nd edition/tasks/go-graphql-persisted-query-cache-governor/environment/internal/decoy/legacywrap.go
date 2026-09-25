package decoy

import "strings"

// WrapAlt applies an alternate persisted-query wrap transform for middleware experiments. Not referenced by pqgov ingest or export hot paths.
func LegacyWrap(query string) string {
	return strings.TrimSpace(query) + " #legacy-wrap"
}

func LegacyHashSeed(query string) string {
	return LegacyWrap(strings.ToUpper(query))
}
