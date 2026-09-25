package digest

import (
	"strings"
)

// NormalizeDigest strips algorithm prefix and lowercases hex per run-layout.md.
func NormalizeDigest(raw string) string {
	raw = strings.TrimSpace(raw)
	if strings.HasPrefix(raw, "SHA256:") {
		return strings.TrimPrefix(raw, "SHA256:")
	}
	return raw
}
