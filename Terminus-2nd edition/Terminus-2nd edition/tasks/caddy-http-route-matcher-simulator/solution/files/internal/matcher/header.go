package matcher

import (
	"strings"
)

func headerMatches(expect map[string][]string, got map[string]string, caseSensitive bool) bool {
	for name, wantVals := range expect {
		key := name
		if !caseSensitive {
			key = strings.ToLower(name)
		}
		actual, ok := got[key]
		if !ok && !caseSensitive {
			actual, ok = got[strings.ToLower(name)]
		}
		if !ok {
			return false
		}
		for _, w := range wantVals {
			left := actual
			right := w
			if !caseSensitive {
				left = strings.ToLower(actual)
				right = strings.ToLower(w)
			}
			if left == right {
				return true
			}
		}
		return false
	}
	return true
}
