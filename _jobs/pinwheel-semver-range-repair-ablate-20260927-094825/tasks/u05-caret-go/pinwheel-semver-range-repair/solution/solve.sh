#!/usr/bin/env bash
set -euo pipefail

cd /app

# Numeric prerelease identifiers must not carry leading zeros (1.2.3-01 is invalid).
cat > /app/internal/semver/version.go <<'GOSRC'
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
		n, ok := ParseNumeric(r)
		if !ok {
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

// SameTriple reports whether v and o differ at most in prerelease and build.
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
GOSRC

# Prerelease precedence: numeric identifiers compare as numbers, and a longer
# identifier list wins when the shorter one is a prefix of it.
cat > /app/internal/semver/compare.go <<'GOSRC'
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
	for i := 0; ; i++ {
		switch {
		case i >= len(a) && i >= len(b):
			return 0
		case i >= len(a):
			return -1
		case i >= len(b):
			return 1
		}
		if c := compareIdentifier(a[i], b[i]); c != 0 {
			return c
		}
	}
}

func compareIdentifier(a, b Identifier) int {
	switch {
	case a.Numeric && b.Numeric:
		return cmpUint(a.Num, b.Num)
	case a.Numeric:
		return -1
	case b.Numeric:
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
GOSRC

# An exact comparator matches on precedence, so build metadata is ignored.
cat > /app/internal/semrange/comparator.go <<'GOSRC'
package semrange

import "github.com/brightloom/pinwheel/internal/semver"

// Op is a comparison operator.
type Op int

const (
	OpEQ Op = iota
	OpLT
	OpLTE
	OpGT
	OpGTE
)

func (o Op) String() string {
	switch o {
	case OpLT:
		return "<"
	case OpLTE:
		return "<="
	case OpGT:
		return ">"
	case OpGTE:
		return ">="
	}
	return ""
}

// Comparator is one primitive condition such as ">=1.2.0" or "<2.0.0-0".
// A comparator with Any set matches every version.
type Comparator struct {
	Op      Op
	Version semver.Version
	Any     bool
}

var (
	matchAll = Comparator{Any: true}
	// matchNone is what "<*" and ">*" reduce to.
	matchNone = Comparator{Op: OpLT, Version: semver.New(0, 0, 0).Floor()}
)

// Test reports whether v satisfies the comparator on its own. Prerelease
// admission is decided per comparator set, see Range.Test.
func (c Comparator) Test(v semver.Version) bool {
	if c.Any {
		return true
	}
	d := semver.Compare(v, c.Version)
	switch c.Op {
	case OpEQ:
		return d == 0
	case OpLT:
		return d < 0
	case OpLTE:
		return d <= 0
	case OpGT:
		return d > 0
	case OpGTE:
		return d >= 0
	}
	return false
}

func (c Comparator) String() string {
	if c.Any {
		return "*"
	}
	return c.Op.String() + c.Version.String()
}
GOSRC

# '||' may have any amount of whitespace around it, and a prerelease is only
# admitted by a set that names a prerelease of the same major.minor.patch.
cat > /app/internal/semrange/range.go <<'GOSRC'
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
	unionSep = regexp.MustCompile(`\s*\|\|\s*`)
	hyphenRe = regexp.MustCompile(`^(\S+)\s+-\s+(\S+)$`)
	opSpace  = regexp.MustCompile(`(~>|<=|>=|[<>=~^])\s+`)
)

// Parse reads a range such as "^1.2.0", ">=1.0.0 <2 || 3.x" or "1.2 - 2.3".
func Parse(s string) (Range, error) {
	r := Range{Raw: s}
	for _, alt := range unionSep.Split(strings.TrimSpace(s), -1) {
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
		if c.Any || !c.Version.IsPrerelease() {
			continue
		}
		if c.Version.SameTriple(v) {
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
GOSRC

# Caret keeps the left-most non-zero field: ^0.2.3 < 0.3.0-0, ^0.0.3 < 0.0.4-0.

# ~1 means >=1.0.0 <2.0.0-0, not ~1.0.
cat > /app/internal/semrange/tilde.go <<'GOSRC'
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
GOSRC

# >1.2 means >=1.3.0 and <=1.2 means <1.3.0-0.
cat > /app/internal/semrange/xrange.go <<'GOSRC'
package semrange

import "github.com/brightloom/pinwheel/internal/semver"

// xrange expands a plain or operator-prefixed partial: "1.2.3", "=1.2.3",
// "1.x", ">1.2", "<=2", "*".
func xrange(op string, p partial) []Comparator {
	if p.fields == 3 {
		return []Comparator{{Op: opFor(op), Version: p.version()}}
	}
	if p.fields == 0 {
		if op == "<" || op == ">" {
			return []Comparator{matchNone}
		}
		return []Comparator{matchAll}
	}
	lo := semver.New(p.major, p.minor, 0)
	switch op {
	case ">":
		return []Comparator{{Op: OpGTE, Version: p.next()}}
	case ">=":
		return []Comparator{{Op: OpGTE, Version: lo}}
	case "<":
		return []Comparator{{Op: OpLT, Version: lo.Floor()}}
	case "<=":
		return []Comparator{{Op: OpLT, Version: p.next().Floor()}}
	}
	return between(lo, p.next())
}

func opFor(op string) Op {
	switch op {
	case "<":
		return OpLT
	case "<=":
		return OpLTE
	case ">":
		return OpGT
	case ">=":
		return OpGTE
	}
	return OpEQ
}
GOSRC

# A partial upper bound covers everything it matches: 1.2 - 2.3 is <2.4.0-0.
cat > /app/internal/semrange/hyphen.go <<'GOSRC'
package semrange

// hyphen expands "from - to". A partial on the left fills missing fields with
// zeros; a partial on the right covers every version it matches.
func hyphen(from, to partial) []Comparator {
	var set []Comparator
	if from.fields > 0 {
		set = append(set, Comparator{Op: OpGTE, Version: from.version()})
	}
	switch {
	case to.fields == 3:
		set = append(set, Comparator{Op: OpLTE, Version: to.version()})
	case to.fields > 0:
		set = append(set, Comparator{Op: OpLT, Version: to.next().Floor()})
	}
	if len(set) == 0 {
		set = append(set, matchAll)
	}
	return set
}
GOSRC

# Each round replaces the selection, so packages nobody requires any more drop out.
cat > /app/internal/resolve/resolver.go <<'GOSRC'
// Package resolve computes the flat set of releases a project locks.
package resolve

import (
	"fmt"

	"github.com/brightloom/pinwheel/internal/manifest"
	"github.com/brightloom/pinwheel/internal/registry"
)

const maxRounds = 100

// Result is a settled resolution.
type Result struct {
	// Selected maps every required package to its locked release.
	Selected map[string]*registry.Release
	// Constraints holds, per package, the ranges its dependents wrote for it.
	Constraints map[string][]Constraint
}

// Resolve runs resolution rounds until the selection stops changing.
func Resolve(m *manifest.Manifest, reg *registry.Registry) (*Result, error) {
	sel := map[string]*registry.Release{}
	for round := 0; round < maxRounds; round++ {
		cons, err := gather(m, sel)
		if err != nil {
			return nil, err
		}
		next := make(map[string]*registry.Release, len(cons))
		for _, name := range sortedKeys(cons) {
			pkg, ok := reg.Package(name)
			if !ok {
				return nil, &UnknownPackageError{Package: name, RequiredBy: dependents(cons[name])}
			}
			rel, err := choose(pkg, effective(m, name, cons[name]), m.PreferLowest())
			if err != nil {
				return nil, err
			}
			next[name] = rel
		}
		if sameSelection(sel, next) {
			return &Result{Selected: next, Constraints: cons}, nil
		}
		sel = next
	}
	return nil, fmt.Errorf("resolution did not settle after %d rounds", maxRounds)
}

func sameSelection(a, b map[string]*registry.Release) bool {
	if len(a) != len(b) {
		return false
	}
	for name, rel := range a {
		if b[name] != rel {
			return false
		}
	}
	return true
}
GOSRC

# An override replaces the dependents' ranges instead of being added to them.
cat > /app/internal/resolve/constraints.go <<'GOSRC'
package resolve

import (
	"fmt"
	"sort"

	"github.com/brightloom/pinwheel/internal/manifest"
	"github.com/brightloom/pinwheel/internal/registry"
	"github.com/brightloom/pinwheel/internal/semrange"
)

const (
	// RootName stands for the project itself as a dependent.
	RootName = "<root>"
	// OverrideName is the source recorded for a constraint from "overrides".
	OverrideName = "<overrides>"
)

// Constraint is one range some dependent placed on a package.
type Constraint struct {
	From  string
	Raw   string
	Range semrange.Range
}

// gather walks from the project's dependencies through the dependencies of
// the selected releases and returns the constraints on every package reached.
// Packages reached but not selected yet contribute no constraints of their own.
func gather(m *manifest.Manifest, sel map[string]*registry.Release) (map[string][]Constraint, error) {
	cons := map[string][]Constraint{}
	var queue []string
	add := func(from, name, raw string) error {
		r, err := semrange.Parse(raw)
		if err != nil {
			return fmt.Errorf("%s depends on %s: %w", from, name, err)
		}
		if _, seen := cons[name]; !seen {
			queue = append(queue, name)
		}
		cons[name] = append(cons[name], Constraint{From: from, Raw: raw, Range: r})
		return nil
	}
	for _, name := range sortedKeys(m.Dependencies) {
		if err := add(RootName, name, m.Dependencies[name]); err != nil {
			return nil, err
		}
	}
	for len(queue) > 0 {
		name := queue[0]
		queue = queue[1:]
		rel, ok := sel[name]
		if !ok {
			continue
		}
		for _, dep := range sortedKeys(rel.Dependencies) {
			if err := add(name, dep, rel.Dependencies[dep]); err != nil {
				return nil, err
			}
		}
	}
	return cons, nil
}

// effective returns the constraints a release of name has to meet.
func effective(m *manifest.Manifest, name string, cons []Constraint) []Constraint {
	raw, ok := m.Overrides[name]
	if !ok {
		return cons
	}
	return []Constraint{{From: OverrideName, Raw: raw, Range: semrange.MustParse(raw)}}
}

func sortedKeys[V any](m map[string]V) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}
GOSRC

# A bare full version is an exact pin too, not only '=VERSION'.
cat > /app/internal/resolve/yanked.go <<'GOSRC'
package resolve

import (
	"github.com/brightloom/pinwheel/internal/registry"
	"github.com/brightloom/pinwheel/internal/semrange"
)

// pinned reports whether one of the constraints pins rel exactly, which is
// the only way a yanked release can still be locked.
func pinned(rel *registry.Release, cons []Constraint) bool {
	for _, c := range cons {
		if exactPin(c.Range) && c.Range.Test(rel.Parsed) {
			return true
		}
	}
	return false
}

func exactPin(r semrange.Range) bool {
	if len(r.Sets) != 1 || len(r.Sets[0]) != 1 {
		return false
	}
	c := r.Sets[0][0]
	return !c.Any && c.Op == semrange.OpEQ
}
GOSRC

# Equal-precedence ties go to the latest published release (then file order)
# whichever way prefer points.
cat > /app/internal/resolve/candidates.go <<'GOSRC'
package resolve

import (
	"github.com/brightloom/pinwheel/internal/registry"
	"github.com/brightloom/pinwheel/internal/semver"
)

// choose picks the release of pkg to lock under the given constraints.
func choose(pkg *registry.Package, cons []Constraint, lowest bool) (*registry.Release, error) {
	var eligible []*registry.Release
	for i := range pkg.Releases {
		rel := &pkg.Releases[i]
		if !satisfiesAll(rel, cons) {
			continue
		}
		if rel.Yanked && !pinned(rel, cons) {
			continue
		}
		eligible = append(eligible, rel)
	}
	if len(eligible) == 0 {
		return nil, &UnsatisfiableError{Package: pkg.Name, Constraints: cons}
	}
	best := eligible[0]
	for _, rel := range eligible[1:] {
		if preferred(rel, best, lowest) {
			best = rel
		}
	}
	return best, nil
}

func satisfiesAll(rel *registry.Release, cons []Constraint) bool {
	for _, c := range cons {
		if !c.Range.Test(rel.Parsed) {
			return false
		}
	}
	return true
}

// preferred reports whether a should be locked instead of b.
func preferred(a, b *registry.Release, lowest bool) bool {
	if c := semver.Compare(a.Parsed, b.Parsed); c != 0 {
		if lowest {
			return c < 0
		}
		return c > 0
	}
	if !a.Published.Equal(b.Published) {
		return a.Published.After(b.Published)
	}
	return a.Index > b.Index
}
GOSRC

# pin.lock is written without HTML escaping ('<root>', '>=1.2' stay as-is).
cat > /app/internal/lockfile/lockfile.go <<'GOSRC'
// Package lockfile builds and writes pin.lock.
package lockfile

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/brightloom/pinwheel/internal/manifest"
	"github.com/brightloom/pinwheel/internal/resolve"
)

// FileName is the lock's name inside a project directory.
const FileName = "pin.lock"

// FormatVersion is written as lockfileVersion.
const FormatVersion = 1

// Lock is the document written to pin.lock. Field order is the output order.
type Lock struct {
	LockfileVersion int              `json:"lockfileVersion"`
	Name            string           `json:"name"`
	Packages        map[string]Entry `json:"packages"`
}

// Entry is one locked package.
type Entry struct {
	Version      string            `json:"version"`
	RequiredBy   []string          `json:"requiredBy"`
	Dependencies map[string]string `json:"dependencies"`
}

// Build turns a resolution into a lock.
func Build(m *manifest.Manifest, res *resolve.Result) *Lock {
	lock := &Lock{LockfileVersion: FormatVersion, Name: m.Name, Packages: map[string]Entry{}}
	for name, rel := range res.Selected {
		deps := make(map[string]string, len(rel.Dependencies))
		for k, v := range rel.Dependencies {
			deps[k] = v
		}
		lock.Packages[name] = Entry{
			Version:      rel.Version,
			RequiredBy:   requiredBy(res.Constraints[name]),
			Dependencies: deps,
		}
	}
	return lock
}

func requiredBy(cons []resolve.Constraint) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, c := range cons {
		if !seen[c.From] {
			seen[c.From] = true
			out = append(out, c.From)
		}
	}
	sort.Strings(out)
	return out
}

// Encode renders the lock exactly as it is stored on disk.
func Encode(l *Lock) ([]byte, error) {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if err := enc.Encode(l); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// Write stores the lock at path, replacing any previous file atomically.
func Write(path string, l *Lock) error {
	data, err := Encode(l)
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".pin.lock-*")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Chmod(tmp.Name(), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}
GOSRC

test -z "$(gofmt -l .)"
go vet ./...
go test ./...
go build -o /usr/local/bin/pinwheel ./cmd/pinwheel
