package rootbind

import "strings"

// MatchGlob reports whether value matches pattern.
//
// Per docs/fulcio-root-bind.md, matching must be a full-string anchored
// glob: '*' stands for any run of characters, and the match must span the
// entire value from start to end (not a substring anywhere inside it).
func MatchGlob(pattern, value string) bool {
	if !strings.Contains(pattern, "*") {
		return pattern == value
	}

	parts := strings.Split(pattern, "*")
	n := len(parts)

	if !strings.HasPrefix(value, parts[0]) {
		return false
	}
	rest := value[len(parts[0]):]

	last := parts[n-1]
	if !strings.HasSuffix(rest, last) {
		return false
	}
	middleSpan := rest[:len(rest)-len(last)]

	pos := 0
	for _, part := range parts[1 : n-1] {
		if part == "" {
			continue
		}
		idx := strings.Index(middleSpan[pos:], part)
		if idx < 0 {
			return false
		}
		pos += idx + len(part)
	}
	return true
}
