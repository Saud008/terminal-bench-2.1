package matcher

import (
	"regexp"
	"strings"
)

func pathRegexpMatches(patterns []string, path string) bool {
	for _, pat := range patterns {
		if pathRegexpSingle(pat, path) {
			return true
		}
	}
	return false
}

func pathRegexpSingle(pat, path string) bool {
	anchored := pat
	if !strings.HasPrefix(anchored, "^") {
		anchored = "^" + anchored
	}
	if !strings.HasSuffix(anchored, "$") {
		anchored = anchored + "$"
	}
	re, err := regexp.Compile(anchored)
	if err != nil {
		return false
	}
	return re.MatchString(path)
}
