// Package semrange parses npm-style version ranges and tests versions
// against them.
package semrange

import (
	"fmt"
	"regexp"
	"strings"

	"github.com/brightloom/pinwheel/internal/semver"
)

// Range is a union of comparator sets. A version satisfies the range when it
// satisfies every comparator of at least one set.
type Range struct {
	Raw  string
	Sets [][]Comparator
}

// ParseError reports text that is not a valid range.
type ParseError struct{ Input string }

func (e *ParseError) Error() string { return fmt.Sprintf("invalid range %q", e.Input) }

var (
	hyphenRe = regexp.MustCompile(`^(\S+)\s+-\s+(\S+)$`)
	opSpace  = regexp.MustCompile(`(~>|<=|>=|[<>=~^])\s+`)
)

// Parse reads a range such as "^1.2.0", ">=1.0.0 <2 || 3.x" or "1.2 - 2.3".
func Parse(s string) (Range, error) {
	r := Range{Raw: s}
	for _, alt := range strings.Split(strings.TrimSpace(s), " || ") {
		set, ok := parseSet(alt)
		if !ok {
			return Range{}, &ParseError{Input: s}
		}
		r.Sets = append(r.Sets, set)
	}
	return r, nil
}

// MustParse is Parse for literals known to be valid.
func MustParse(s string) Range {
	r, err := Parse(s)
	if err != nil {
		panic(err)
	}
	return r
}

func parseSet(alt string) ([]Comparator, bool) {
	alt = strings.TrimSpace(alt)
	if alt == "" {
		return []Comparator{matchAll}, true
	}
	if m := hyphenRe.FindStringSubmatch(alt); m != nil {
		from, ok1 := parsePartial(m[1])
		to, ok2 := parsePartial(m[2])
		if !ok1 || !ok2 {
			return nil, false
		}
		return hyphen(from, to), true
	}
	var set []Comparator
	for _, tok := range strings.Fields(opSpace.ReplaceAllString(alt, "$1")) {
		cs, ok := parseToken(tok)
		if !ok {
			return nil, false
		}
		set = append(set, cs...)
	}
	return set, true
}

func parseToken(tok string) ([]Comparator, bool) {
	var expand func(partial) []Comparator
	switch {
	case strings.HasPrefix(tok, "~>"):
		tok, expand = tok[2:], tilde
	case strings.HasPrefix(tok, "~"):
		tok, expand = tok[1:], tilde
	case strings.HasPrefix(tok, "^"):
		tok, expand = tok[1:], caret
	default:
		op, rest := splitOp(tok)
		p, ok := parsePartial(rest)
		if !ok {
			return nil, false
		}
		return xrange(op, p), true
	}
	p, ok := parsePartial(tok)
	if !ok {
		return nil, false
	}
	return expand(p), true
}

func splitOp(tok string) (string, string) {
	for _, op := range []string{"<=", ">=", "<", ">", "="} {
		if strings.HasPrefix(tok, op) {
			return op, tok[len(op):]
		}
	}
	return "", tok
}

// Test reports whether v satisfies r.
func (r Range) Test(v semver.Version) bool {
	for _, set := range r.Sets {
		if testSet(set, v) {
			return true
		}
	}
	return false
}

func testSet(set []Comparator, v semver.Version) bool {
	for _, c := range set {
		if !c.Test(v) {
			return false
		}
	}
	if !v.IsPrerelease() {
		return true
	}
	for _, c := range set {
		if !c.Any && c.Version.IsPrerelease() {
			return true
		}
	}
	return false
}

func (r Range) String() string {
	alts := make([]string, len(r.Sets))
	for i, set := range r.Sets {
		parts := make([]string, len(set))
		for j, c := range set {
			parts[j] = c.String()
		}
		alts[i] = strings.Join(parts, " ")
	}
	return strings.Join(alts, " || ")
}
