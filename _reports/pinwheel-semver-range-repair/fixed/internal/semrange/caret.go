package semrange

import "github.com/brightloom/pinwheel/internal/semver"

// caret expands "^p": changes that do not modify the left-most non-zero
// field of p.
func caret(p partial) []Comparator {
	switch p.fields {
	case 0:
		return []Comparator{matchAll}
	case 1:
		return between(semver.New(p.major, 0, 0), semver.New(p.major+1, 0, 0))
	case 2:
		if p.major == 0 {
			return between(semver.New(0, p.minor, 0), semver.New(0, p.minor+1, 0))
		}
		return between(semver.New(p.major, p.minor, 0), semver.New(p.major+1, 0, 0))
	}
	lo := p.version()
	switch {
	case p.major > 0:
		return between(lo, semver.New(p.major+1, 0, 0))
	case p.minor > 0:
		return between(lo, semver.New(0, p.minor+1, 0))
	}
	return between(lo, semver.New(0, 0, p.patch+1))
}
