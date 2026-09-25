package dn

import "strings"

// NormalizeDN canonicalizes a distinguished name for shadow keys.
func NormalizeDN(raw string) string {
	return strings.ToLower(strings.TrimSpace(raw))
}
