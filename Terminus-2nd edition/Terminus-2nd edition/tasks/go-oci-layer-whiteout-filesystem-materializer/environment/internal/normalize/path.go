package normalize

import (
	"strings"
)

// CleanPath normalizes OCI layer paths for staging ledger records.
func CleanPath(raw string) string {
	p := strings.TrimSpace(raw)
	if p == "" {
		return "/"
	}
	if !strings.HasPrefix(p, "/") {
		p = "/" + p
	}
	return strings.TrimRight(p, "/")
}
