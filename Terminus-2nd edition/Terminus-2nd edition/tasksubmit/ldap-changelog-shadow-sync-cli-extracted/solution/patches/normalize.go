package dn

import "strings"

// NormalizeDN canonicalizes a distinguished name for shadow keys.
func NormalizeDN(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ""
	}
	parts := splitRDN(raw)
	for i, part := range parts {
		eq := indexUnescapedEquals(part)
		if eq < 0 {
			parts[i] = strings.ToLower(part)
			continue
		}
		attr := strings.ToLower(strings.TrimSpace(part[:eq]))
		val := strings.TrimSpace(part[eq+1:])
		parts[i] = attr + "=" + val
	}
	return strings.Join(parts, ",")
}

func splitRDN(dn string) []string {
	var parts []string
	start := 0
	for i := 0; i < len(dn); i++ {
		if dn[i] == '\\' {
			i++
			continue
		}
		if dn[i] == ',' {
			parts = append(parts, dn[start:i])
			start = i + 1
		}
	}
	parts = append(parts, dn[start:])
	return parts
}

func indexUnescapedEquals(s string) int {
	for i := 0; i < len(s); i++ {
		if s[i] == '\\' {
			i++
			continue
		}
		if s[i] == '=' {
			return i
		}
	}
	return -1
}
