package cache

import "strings"

func CacheKey(domain, name string) string {
	return strings.ToLower(domain) + "\x00" + name
}
