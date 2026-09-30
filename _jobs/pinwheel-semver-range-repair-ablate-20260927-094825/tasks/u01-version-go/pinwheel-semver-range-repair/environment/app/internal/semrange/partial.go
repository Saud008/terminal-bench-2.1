package semrange

import (
	"regexp"

	"github.com/brightloom/pinwheel/internal/semver"
)

// partial is a version as written inside a range, where trailing fields may be
// missing or wildcards: "1", "1.2", "1.2.x", "*", "1.2.3-beta.1".
type partial struct {
	major, minor, patch uint64
	// fields counts the concrete leading fields (0 for "*", 3 for a full version).
	fields int
	pre    []semver.Identifier
}

var partialRe = regexp.MustCompile(`^[v=]*` +
	`(\*|x|X|0|[1-9][0-9]*)` +
	`(?:\.(\*|x|X|0|[1-9][0-9]*)` +
	`(?:\.(\*|x|X|0|[1-9][0-9]*)` +
	`(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?` +
	`(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?)?)?$`)

func isWild(s string) bool { return s == "" || s == "x" || s == "X" || s == "*" }

func parsePartial(s string) (partial, bool) {
	m := partialRe.FindStringSubmatch(s)
	if m == nil {
		return partial{}, false
	}
	var p partial
	dst := [3]*uint64{&p.major, &p.minor, &p.patch}
	for i, f := range m[1:4] {
		if isWild(f) {
			break
		}
		n, ok := semver.ParseNumeric(f)
		if !ok {
			return partial{}, false
		}
		*dst[i] = n
		p.fields++
	}
	if p.fields == 3 && m[4] != "" {
		pre, ok := semver.ParsePrerelease(m[4])
		if !ok {
			return partial{}, false
		}
		p.pre = pre
	}
	return p, true
}

// version fills missing fields with zero. The prerelease is only kept for a
// full version; build metadata is never kept.
func (p partial) version() semver.Version {
	v := semver.New(p.major, p.minor, p.patch)
	if p.fields == 3 {
		v.Pre = p.pre
	}
	return v
}

// next is the first release above everything a one- or two-field partial
// covers: "1" -> 2.0.0, "1.2" -> 1.3.0.
func (p partial) next() semver.Version {
	if p.fields == 1 {
		return semver.New(p.major+1, 0, 0)
	}
	return semver.New(p.major, p.minor+1, 0)
}

// between is ">=lo <hi-0": everything from lo up to, but excluding, every
// version of hi's major.minor.patch including its prereleases.
func between(lo, hi semver.Version) []Comparator {
	return []Comparator{{Op: OpGTE, Version: lo}, {Op: OpLT, Version: hi.Floor()}}
}
