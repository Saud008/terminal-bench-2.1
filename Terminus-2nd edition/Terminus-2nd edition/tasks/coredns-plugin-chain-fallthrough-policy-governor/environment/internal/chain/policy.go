package chain

import "strings"

// AllowsFallthroughPolicy is a legacy helper kept for compatibility audits.
// The live chain uses AllowsFallthrough in fallthrough.go.
func AllowsFallthroughPolicy(zone, qname string, enabled bool) bool {
	if !enabled {
		return false
	}
	z := strings.TrimSuffix(strings.ToLower(zone), ".")
	q := strings.TrimSuffix(strings.ToLower(qname), ".")
	if strings.HasSuffix(q, "."+z) {
		return false
	}
	return true
}
