// Package version handles the core version quire emulates and the -b
// compatibility version requested on the command line.
package version

import (
	"fmt"
	"strings"

	"quire/internal/ctext"
)

// Version is a major.minor.patch triple.
type Version struct {
	Major, Minor, Patch int
}

// Current is the EditorConfig core version whose behaviour quire reproduces.
var Current = Version{0, 12, 6}

// TabIndent is the first version that derives indent_size from
// indent_style = tab and resolves indent_size = tab through tab_width.
var TabIndent = Version{0, 9, 0}

func (v Version) String() string {
	return fmt.Sprintf("%d.%d.%d", v.Major, v.Minor, v.Patch)
}

// Compare returns -1, 0 or +1 comparing v with o.
func (v Version) Compare(o Version) int {
	return strings.Compare(v.String(), o.String())
}

// Request collects the components given with -b. A negative component was
// not given.
type Request struct {
	Major, Minor, Patch int
}

// NoRequest is the state before any -b option.
var NoRequest = Request{-1, -1, -1}

// Apply reads a -b argument into r. Components are separated by dots (empty
// components are skipped) and read like strtol. It reports false when the
// argument has more than three components; the components before the fourth
// have been stored by then.
func (r *Request) Apply(arg string) bool {
	pos := 0
	for _, tok := range strings.Split(arg, ".") {
		if tok == "" {
			continue
		}
		n := ctext.Atoi(tok)
		switch pos {
		case 0:
			r.Major = n
		case 1:
			r.Minor = n
		case 2:
			r.Patch = n
		default:
			return false
		}
		pos++
	}
	return true
}

// Effective is the version a file is resolved with: components that were not
// given (or are negative) count as 0, and 0.0.0 means Current.
func (r Request) Effective() Version {
	v := Version{max(r.Major, 0), max(r.Minor, 0), max(r.Patch, 0)}
	if v == (Version{}) {
		return Current
	}
	return v
}
