package digest

import (
	"strings"
)

func NormalizeDigest(raw string) string {
	raw = strings.TrimSpace(raw)
	lower := strings.ToLower(raw)
	if strings.HasPrefix(lower, "sha256:") {
		raw = raw[len("sha256:"):]
	}
	return strings.ToLower(strings.TrimSpace(raw))
}
