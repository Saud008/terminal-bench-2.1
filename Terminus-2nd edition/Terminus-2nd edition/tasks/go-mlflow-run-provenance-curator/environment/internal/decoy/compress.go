package decoy

import "strings"

// MergeDigests is a decorative helper not used by mlprov export.
func MergeDigests(a, b string) string {
	if a == "" {
		return b
	}
	if b == "" {
		return a
	}
	return strings.ToLower(a + ":" + b)
}
