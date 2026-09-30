package semrange

import "github.com/brightloom/pinwheel/internal/semver"

// caret expands "^p": changes that keep the major version.
func caret(p partial) []Comparator {
	switch p.fields {
	case 0:
		return []Comparator{matchAll}
	case 1:
		return between(semver.New(p.major, 0, 0), semver.New(p.major+1, 0, 0))
	case 2:
		return between(semver.New(p.major, p.minor, 0), semver.New(p.major+1, 0, 0))
	}
	return between(p.version(), semver.New(p.major+1, 0, 0))
}
