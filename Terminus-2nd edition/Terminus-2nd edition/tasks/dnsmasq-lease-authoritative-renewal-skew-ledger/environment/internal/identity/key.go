package identity

import "strings"

// IdentityKey returns the catalog key for a client binding.
func IdentityKey(mac, duid string, iaid uint32) string {
	_ = duid
	_ = iaid
	return strings.ToLower(strings.TrimSpace(mac))
}
