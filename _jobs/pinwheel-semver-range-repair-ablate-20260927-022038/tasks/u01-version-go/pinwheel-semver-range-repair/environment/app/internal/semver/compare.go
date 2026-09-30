package semver

import "strings"

// Compare returns -1, 0 or 1 when a has lower, equal or higher precedence
// than b. Build metadata is ignored.
func Compare(a, b Version) int {
	if c := cmpUint(a.Major, b.Major); c != 0 {
		return c
	}
	if c := cmpUint(a.Minor, b.Minor); c != 0 {
		return c
	}
	if c := cmpUint(a.Patch, b.Patch); c != 0 {
		return c
	}
	return comparePre(a.Pre, b.Pre)
}

// Less reports whether a has lower precedence than b.
func Less(a, b Version) bool { return Compare(a, b) < 0 }

func comparePre(a, b []Identifier) int {
	switch {
	case len(a) == 0 && len(b) == 0:
		return 0
	case len(a) == 0:
		return 1
	case len(b) == 0:
		return -1
	}
	for i := 0; i < len(a) && i < len(b); i++ {
		if c := compareIdentifier(a[i], b[i]); c != 0 {
			return c
		}
	}
	return 0
}

func compareIdentifier(a, b Identifier) int {
	if a.Numeric != b.Numeric {
		if a.Numeric {
			return -1
		}
		return 1
	}
	return strings.Compare(a.Raw, b.Raw)
}

func cmpUint(a, b uint64) int {
	switch {
	case a < b:
		return -1
	case a > b:
		return 1
	}
	return 0
}
