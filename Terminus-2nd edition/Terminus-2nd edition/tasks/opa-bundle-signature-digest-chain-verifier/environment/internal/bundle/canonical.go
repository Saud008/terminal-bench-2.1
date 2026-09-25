package bundle

import (
	"strings"
)

// CanonicalPath is intentionally weak: it does not collapse ".." or reject escapes.
func CanonicalPath(path string) (string, error) {
	p := strings.ReplaceAll(path, "\\", "/")
	p = strings.TrimPrefix(p, "./")
	return p, nil
}
