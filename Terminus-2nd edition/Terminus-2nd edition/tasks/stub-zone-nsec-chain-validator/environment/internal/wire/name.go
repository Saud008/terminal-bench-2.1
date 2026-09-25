package wire

import (
	"strings"
)

// Canonical lowercases ASCII A-Z in DNS names for ordering comparisons.
func Canonical(name string) string {
	name = strings.TrimSpace(name)
	if name == "" {
		return name
	}
	var b strings.Builder
	for _, ch := range name {
		if ch >= 'A' && ch <= 'Z' {
			b.WriteRune(ch + ('a' - 'A'))
		} else {
			b.WriteRune(ch)
		}
	}
	return b.String()
}

func EnsureTrailingDot(name string) string {
	name = strings.TrimSpace(name)
	if name == "" {
		return name
	}
	if !strings.HasSuffix(name, ".") {
		return name + "."
	}
	return name
}
