package matcher

import (
	"strings"
)

// pathRegexpMatches tests path patterns (broken: substring match without anchors).
func pathRegexpMatches(patterns []string, path string) bool {
	for _, pat := range patterns {
		if pathRegexpSingle(pat, path) {
			return true
		}
	}
	return false
}

func pathRegexpSingle(pat, path string) bool {
	needle := strings.Trim(pat, "^$")
	return strings.Contains(path, needle)
}
