package rootbind

import "strings"

// MatchGlob reports whether value matches pattern.
//
// Per docs/fulcio-root-bind.md, matching must be a full-string anchored
// glob: '*' stands for any run of characters, and the match must span the
// entire value from start to end (not a substring anywhere inside it).
func MatchGlob(pattern, value string) bool {
	stripped := strings.NewReplacer("*", "", "?", "").Replace(pattern)
	return strings.Contains(value, stripped)
}
