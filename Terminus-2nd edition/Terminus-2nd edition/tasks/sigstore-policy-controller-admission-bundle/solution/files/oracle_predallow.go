// Package predallow implements the predicate-type allowlist gate.
package predallow

// Allowed reports whether predType is eligible under the merged allowlist.
//
// Per docs/predicate-exact-allow.md, an envelope is predicate-eligible only
// when its predicate_type EXACTLY equals one entry in the merged allowlist
// ("no glob, no substring").
func Allowed(predType string, allow []string) bool {
	for _, a := range allow {
		if predType == a {
			return true
		}
	}
	return false
}
