// Package semver parses and orders Semantic Versioning 2.0.0 versions.
package semver

import (
	"fmt"
	"strconv"
	"strings"
)

// maxSafe is the largest value npm tooling accepts in a numeric field
// (JavaScript's Number.MAX_SAFE_INTEGER).
const maxSafe = 1<<53 - 1

// Identifier is one dot-separated prerelease identifier.
type Identifier struct {
	Raw     string
	Numeric bool
	Num     uint64
}

// Version is a parsed version. Build metadata is kept so it can be printed
// again, but it has no influence on precedence.
type Version struct {
	Major, Minor, Patch uint64
	Pre                 []Identifier
	Build               []string
}

// ParseError reports text that is not a valid version.
type ParseError struct{ Input string }

func (e *ParseError) Error() string { return fmt.Sprintf("invalid version %q", e.Input) }

// Parse reads a full version such as "1.4.0", "v2.0.0-rc.1" or "1.0.0+sha.5114f85".
func Parse(s string) (Version, error) {
	body := strings.TrimPrefix(strings.TrimSpace(s), "v")
	v, ok := parse(body)
	if !ok {
		return Version{}, &ParseError{Input: s}
	}
	return v, nil
}

// MustParse is Parse for literals known to be valid.
func MustParse(s string) Version {
	v, err := Parse(s)
	if err != nil {
		panic(err)
	}
	return v
}

func parse(s string) (Version, bool) {
	var v Version
	if i := strings.IndexByte(s, '+'); i >= 0 {
		build, ok := splitIdentifiers(s[i+1:])
		if !ok {
			return v, false
		}
		v.Build = build
		s = s[:i]
	}
	if i := strings.IndexByte(s, '-'); i >= 0 {
		pre, ok := ParsePrerelease(s[i+1:])
		if !ok {
			return v, false
		}
		v.Pre = pre
		s = s[:i]
	}
	parts := strings.Split(s, ".")
	if len(parts) != 3 {
		return v, false
	}
	fields := [3]*uint64{&v.Major, &v.Minor, &v.Patch}
	for i, p := range parts {
		n, ok := ParseNumeric(p)
		if !ok {
			return v, false
		}
		*fields[i] = n
	}
	return v, true
}

// ParsePrerelease parses the part of a version after the first '-'.
func ParsePrerelease(s string) ([]Identifier, bool) {
	raw, ok := splitIdentifiers(s)
	if !ok {
		return nil, false
	}
	ids := make([]Identifier, 0, len(raw))
	for _, r := range raw {
		if !isDigits(r) {
			ids = append(ids, Identifier{Raw: r})
			continue
		}
		n, err := strconv.ParseUint(r, 10, 64)
		if err != nil {
			return nil, false
		}
		ids = append(ids, Identifier{Raw: r, Numeric: true, Num: n})
	}
	return ids, true
}

// ParseNumeric parses a numeric field: ASCII digits, no leading zeros.
func ParseNumeric(s string) (uint64, bool) {
	if !isDigits(s) || (len(s) > 1 && s[0] == '0') {
		return 0, false
	}
	n, err := strconv.ParseUint(s, 10, 64)
	if err != nil || n > maxSafe {
		return 0, false
	}
	return n, true
}

func splitIdentifiers(s string) ([]string, bool) {
	ids := strings.Split(s, ".")
	for _, id := range ids {
		if id == "" {
			return nil, false
		}
		for i := 0; i < len(id); i++ {
			c := id[i]
			if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c == '-') {
				return nil, false
			}
		}
	}
	return ids, true
}

func isDigits(s string) bool {
	if s == "" {
		return false
	}
	for i := 0; i < len(s); i++ {
		if s[i] < '0' || s[i] > '9' {
			return false
		}
	}
	return true
}

// New builds a release version with no prerelease or build part.
func New(major, minor, patch uint64) Version {
	return Version{Major: major, Minor: minor, Patch: patch}
}

// Floor returns the lowest version with the same major.minor.patch, which is
// the "-0" prerelease of that triple.
func (v Version) Floor() Version {
	return Version{Major: v.Major, Minor: v.Minor, Patch: v.Patch, Pre: []Identifier{{Raw: "0", Numeric: true}}}
}

// IsPrerelease reports whether v carries a prerelease part.
func (v Version) IsPrerelease() bool { return len(v.Pre) > 0 }

// SameTriple reports whether v and o share major, minor and patch.
func (v Version) SameTriple(o Version) bool {
	return v.Major == o.Major && v.Minor == o.Minor && v.Patch == o.Patch
}

// Equal reports whether v and o are the same version string, build metadata
// included. Use Compare for precedence.
func (v Version) Equal(o Version) bool { return v.String() == o.String() }

func (v Version) String() string {
	var b strings.Builder
	fmt.Fprintf(&b, "%d.%d.%d", v.Major, v.Minor, v.Patch)
	for i, id := range v.Pre {
		if i == 0 {
			b.WriteByte('-')
		} else {
			b.WriteByte('.')
		}
		b.WriteString(id.Raw)
	}
	if len(v.Build) > 0 {
		b.WriteByte('+')
		b.WriteString(strings.Join(v.Build, "."))
	}
	return b.String()
}
