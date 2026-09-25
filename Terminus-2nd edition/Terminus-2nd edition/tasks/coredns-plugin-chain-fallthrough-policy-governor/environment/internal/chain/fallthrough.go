package chain

import "strings"

func AllowsFallthrough(zone, qname string, enabled bool) bool {
	if !enabled {
		return false
	}
	z := strings.TrimSuffix(strings.ToLower(zone), ".")
	q := strings.TrimSuffix(strings.ToLower(qname), ".")
	if q == z {
		return false
	}
	return true
}
