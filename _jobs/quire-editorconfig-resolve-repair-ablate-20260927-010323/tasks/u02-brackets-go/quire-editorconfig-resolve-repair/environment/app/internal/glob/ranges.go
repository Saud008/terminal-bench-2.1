package glob

import (
	"regexp"
	"strings"

	"quire/internal/ctext"
)

// numRange is a {lo..hi} group; the number it captured must lie in [lo, hi].
type numRange struct {
	lo, hi int
}

var numRangeGroup = regexp.MustCompile(`^\{[+\-]?\d+\.\.[+\-]?\d+\}$`)

// numberPattern captures the number matched in place of a {lo..hi} group.
const numberPattern = `([\+\-]?\d+)`

// parseRange reads a brace group such as "{-3..12}".
func parseRange(group string) (numRange, bool) {
	if !numRangeGroup.MatchString(group) {
		return numRange{}, false
	}
	dots := strings.Index(group, "..")
	return numRange{ctext.Atoi(group[1:]), ctext.Atoi(group[dots+2:])}, true
}

// accepts reports whether the captured text is a number inside the range.
// A number written with a leading zero, including 0 itself, never matches.
func (r numRange) accepts(text string) bool {
	if text == "" || text[0] == '0' {
		return false
	}
	n := ctext.Atoi(text)
	return n >= r.lo && n <= r.hi
}
