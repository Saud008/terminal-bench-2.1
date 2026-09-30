package semrange

import "github.com/brightloom/pinwheel/internal/semver"

// tilde expands "~p": patch-level changes when a minor version is given,
// minor-level changes when only the major is.
func tilde(p partial) []Comparator {
	switch p.fields {
	case 0:
		return []Comparator{matchAll}
	case 1:
		return between(semver.New(p.major, 0, 0), semver.New(p.major+1, 0, 0))
	case 2:
		return between(semver.New(p.major, p.minor, 0), semver.New(p.major, p.minor+1, 0))
	}
	return between(p.version(), semver.New(p.major, p.minor+1, 0))
}
