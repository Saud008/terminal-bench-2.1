package cache

import "strings"

// CacheKey canonicalizes principal identity for the negative/positive maps.
func CacheKey(domain, name string) string {
	return strings.ToLower(domain + name)
}
