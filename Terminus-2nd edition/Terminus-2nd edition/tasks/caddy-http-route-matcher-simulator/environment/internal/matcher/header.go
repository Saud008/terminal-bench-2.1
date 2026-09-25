package matcher

import (
	"strings"
)

// headerMatches compares header maps (broken: folds name only, not value).
func headerMatches(expect map[string][]string, got map[string]string, caseSensitive bool) bool {
	for name, wantVals := range expect {
		key := strings.ToLower(name)
		actual, ok := got[key]
		if !ok {
			actual, ok = got[name]
		}
		if !ok {
			return false
		}
		for _, w := range wantVals {
			if actual == w {
				return true
			}
		}
		return false
	}
	return true
}
