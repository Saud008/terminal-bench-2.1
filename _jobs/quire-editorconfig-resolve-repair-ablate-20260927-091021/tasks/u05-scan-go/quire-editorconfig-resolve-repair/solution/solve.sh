#!/usr/bin/env bash
set -euo pipefail

cd /app

cat > internal/cli/run.go <<'QUIRE_EOF'
// Package cli implements the quire command line.
package cli

import (
	"bufio"
	"fmt"
	"io"

	"quire/internal/resolve"
)

// Main runs quire and returns its exit status.
func Main(argv []string, stdin io.Reader, stdout, stderr io.Writer) int {
	out := bufio.NewWriter(stdout)
	defer out.Flush()

	opts, code, done := parseArgs(argv, out, stderr)
	if done {
		return code
	}
	ro := resolve.Options{ConfName: opts.confName, Version: opts.version.Effective()}
	headers := len(opts.paths) > 1
	in := newInputs(opts.paths, stdin)
	for {
		f, ok := in.next()
		if !ok {
			return 0
		}
		if headers || f.fromStdin {
			fmt.Fprintf(out, "[%s]\n", f.name)
		}
		pairs, err := resolve.File(f.name, ro)
		if err != nil {
			out.Flush()
			fmt.Fprintln(stderr, err)
			return 1
		}
		for _, p := range pairs {
			fmt.Fprintf(out, "%s=%s\n", p.Name, p.Value)
		}
	}
}
QUIRE_EOF

cat > internal/glob/brackets.go <<'QUIRE_EOF'
package glob

import "bytes"

// openBracket translates the '[' at p[i], outside any class. A bracket
// expression containing '/' is taken literally up to its first ']'. It
// returns the regexp text, the index of the last byte consumed, whether a
// character class is now open, and whether the text is a literal copy.
func openBracket(p []byte, i int) (text string, last int, inClass, literal bool) {
	if bracketHasSlash(p, i) {
		end := bytes.IndexByte(p[i:], ']')
		if end < 0 {
			return `\` + string(p[i:]), len(p) - 1, false, true
		}
		end += i
		return `\` + string(p[i:end]) + `\]`, end, false, true
	}
	if i+1 < len(p) && p[i+1] == '!' {
		return "[^", i + 1, true, false
	}
	return "[", i, true, false
}

// bracketHasSlash reports whether a '/' occurs between p[i] and the next
// unescaped ']'.
func bracketHasSlash(p []byte, i int) bool {
	for j := i; j < len(p) && p[j] != ']'; j++ {
		if p[j] == '\\' && j+1 < len(p) {
			j++
			continue
		}
		if p[j] == '/' {
			return true
		}
	}
	return false
}
QUIRE_EOF

cat > internal/glob/compile.go <<'QUIRE_EOF'
// Package glob matches file paths against EditorConfig section globs by
// translating each glob into an anchored regular expression.
package glob

import (
	"bytes"
	"regexp"
	"strings"

	"quire/internal/ctext"
)

// maxRegexp bounds the translated expression, counted the way the C core
// counts its PCRE pattern buffer. Longer translations never match.
const maxRegexp = 2 * 4097

// Matcher is a compiled section glob.
type Matcher struct {
	re     *regexp.Regexp
	ranges []numRange
}

// Match reports whether name matches pattern. A pattern that cannot be
// translated or compiled matches nothing.
func Match(pattern, name string) bool {
	m, ok := Compile(pattern)
	return ok && m.Match(name)
}

// Compile translates pattern.
func Compile(pattern string) (*Matcher, bool) {
	expr, ranges, ok := translate([]byte(pattern))
	if !ok {
		return nil, false
	}
	re, err := regexp.Compile(expr)
	if err != nil {
		return nil, false
	}
	return &Matcher{re: re, ranges: ranges}, true
}

// Match reports whether name matches. Every {lo..hi} group must have
// captured a number inside its range.
func (m *Matcher) Match(name string) bool {
	idx := m.re.FindStringSubmatchIndex(name)
	if idx == nil {
		return false
	}
	for k, r := range m.ranges {
		g := 2 * (k + 1)
		if g+1 >= len(idx) || idx[g] < 0 {
			return false
		}
		if !r.accepts(name[idx[g]:idx[g+1]]) {
			return false
		}
	}
	return true
}

type builder struct {
	out  strings.Builder
	size int
	ok   bool
}

// add appends text whose length in the C core's buffer is size.
func (b *builder) add(text string, size int) {
	if b.size+size >= maxRegexp {
		b.ok = false
	}
	b.out.WriteString(text)
	b.size += size
}

func translate(p []byte) (string, []numRange, bool) {
	paired := bracesPaired(p)
	b := &builder{size: 1, ok: true}
	b.out.WriteString("^")
	var ranges []numRange
	depth := 0
	inClass := false
	for i := 0; i < len(p) && b.ok; i++ {
		c := p[i]
		switch c {
		case '\\':
			if i+1 < len(p) {
				i++
				b.add(escapedPair(p[i]), 2)
			} else {
				b.add(`\\`, 2)
			}
		case '?':
			b.add(`[^/]`, 4)
		case '*':
			if i+1 < len(p) && p[i+1] == '*' {
				b.add(`.*`, 2)
				i++
			} else {
				b.add(`[^\/]*`, 6)
			}
		case '[':
			if inClass {
				b.add(`\[`, 2)
				break
			}
			text, last, cls, literal := openBracket(p, i)
			if literal {
				b.out.WriteString(text)
				b.size += len(text)
			} else {
				b.add(text, len(text))
			}
			i, inClass = last, cls
		case ']':
			inClass = false
			b.add("]", 1)
		case '-':
			if inClass {
				b.add("-", 1)
			} else {
				b.add(`\-`, 2)
			}
		case '{':
			if !paired {
				b.add(`\{`, 2)
				break
			}
			if end, single := singleBrace(p, i); single {
				if r, ok := parseRange(string(p[i : end+1])); ok {
					ranges = append(ranges, r)
					b.add(numberPattern, len(numberPattern))
					i = end
					break
				}
				b.add(`\{`, 2)
				p = insertByte(p, end, '\\')
				break
			}
			depth++
			b.add(`(?:`, 3)
		case '}':
			if !paired {
				b.add(`\}`, 2)
				break
			}
			depth--
			b.add(")", 1)
		case ',':
			if depth > 0 {
				b.add("|", 1)
			} else {
				b.add(`\,`, 2)
			}
		case '/':
			if bytes.HasPrefix(p[i:], []byte("/**/")) {
				b.add(`(\/|\/.*\/)`, 11)
				i += 3
			} else {
				b.add(`\/`, 2)
			}
		default:
			if ctext.IsAlnum(c) {
				b.add(string([]byte{c}), 1)
			} else {
				b.add(quoteByte(c), 2)
			}
		}
	}
	if !b.ok {
		return "", nil, false
	}
	return b.out.String() + "$", ranges, true
}
QUIRE_EOF

cat > internal/glob/literal.go <<'QUIRE_EOF'
package glob

import (
	"fmt"
	"strings"

	"quire/internal/ctext"
)

// Special lists the bytes that have a meaning in a section glob.
const Special = `?[]\*-{},`

// EscapeDir escapes the glob-special bytes of a directory path so that the
// path matches only itself when a section glob is appended to it.
func EscapeDir(dir string) string {
	var b strings.Builder
	for i := 0; i < len(dir); i++ {
		if strings.IndexByte(Special, dir[i]) >= 0 {
			b.WriteByte('\\')
		}
		b.WriteByte(dir[i])
	}
	return b.String()
}

// isPunct reports whether RE2 accepts c after a backslash as a literal.
func isPunct(c byte) bool {
	return c >= '!' && c <= '/' || c >= ':' && c <= '@' || c >= '[' && c <= '`' || c >= '{' && c <= '~'
}

// quoteByte returns the regexp text that matches the byte c literally.
func quoteByte(c byte) string {
	switch {
	case ctext.IsAlnum(c), c >= 0x80:
		return string([]byte{c})
	case isPunct(c):
		return `\` + string([]byte{c})
	default:
		return fmt.Sprintf(`\x{%02x}`, c)
	}
}

// escapedPair returns the regexp text for a backslash followed by c, which
// the core passes to the regexp engine unchanged.
func escapedPair(c byte) string {
	if ctext.IsAlnum(c) {
		return `\` + string([]byte{c})
	}
	return quoteByte(c)
}
QUIRE_EOF


cat > internal/props/fold.go <<'QUIRE_EOF'
package props

import "quire/internal/ctext"

// folded lists the properties whose values are case-insensitive.
var folded = map[string]bool{
	"end_of_line":              true,
	"indent_style":             true,
	"indent_size":              true,
	"insert_final_newline":     true,
	"trim_trailing_whitespace": true,
	"charset":                  true,
}

func foldValue(name, value string) string {
	if folded[name] {
		return ctext.Lower(value)
	}
	return value
}
QUIRE_EOF

cat > internal/props/store.go <<'QUIRE_EOF'
// Package props keeps the properties collected for one file.
package props

import "quire/internal/ctext"

// Pair is one property as printed.
type Pair struct {
	Name, Value string
}

// Store is an ordered set of properties keyed by lowercased name.
type Store struct {
	pairs []Pair
}

// Set records a property. Names are case-insensitive and stored lowercased;
// values of the properties listed in folded are lowercased too. Setting a
// name that is already present replaces its value where it stands.
func (s *Store) Set(name, value string) {
	name = ctext.Lower(name)
	value = foldValue(name, value)
	for i := range s.pairs {
		if s.pairs[i].Name == name {
			s.pairs[i].Value = value
			return
		}
	}
	s.pairs = append(s.pairs, Pair{name, value})
}

// Get returns the value stored for a lowercased name.
func (s *Store) Get(name string) (string, bool) {
	for _, p := range s.pairs {
		if p.Name == name {
			return p.Value, true
		}
	}
	return "", false
}

// Reset forgets every property.
func (s *Store) Reset() {
	s.pairs = nil
}

// Pairs returns the properties in output order.
func (s *Store) Pairs() []Pair {
	return s.pairs
}
QUIRE_EOF

cat > internal/resolve/resolve.go <<'QUIRE_EOF'
// Package resolve computes the EditorConfig properties for one file.
package resolve

import (
	"strings"

	"quire/internal/ctext"
	"quire/internal/glob"
	"quire/internal/ini"
	"quire/internal/props"
	"quire/internal/version"
)

// DefaultConfName is the EditorConfig file name used without -f.
const DefaultConfName = ".editorconfig"

// Options control one resolution.
type Options struct {
	ConfName string
	Version  version.Version
}

type walker struct {
	full  string
	dir   string
	store props.Store
}

// File returns the properties for the file at full, in output order.
func File(full string, o Options) ([]props.Pair, error) {
	if o.Version.Compare(version.Current) > 0 {
		return nil, ErrVersionTooNew
	}
	if !strings.HasPrefix(full, "/") {
		return nil, ErrNotFullPath
	}
	w := &walker{full: full}
	for _, conf := range configPaths(full, o.ConfName) {
		w.dir = dirOf(conf)
		line, err := ini.ParseFile(conf, w.property)
		if err != nil {
			continue
		}
		if line != 0 {
			return nil, &ParseError{Line: line, File: conf}
		}
	}
	props.Derive(&w.store, o.Version)
	return w.store.Pairs(), nil
}

// property handles one name/value pair from the file in w.dir. root = true
// in the preamble discards everything collected from the files above.
func (w *walker) property(section, name, value string) {
	if section == "" && ctext.EqualFold(name, "root") && ctext.EqualFold(value, "true") {
		w.store.Reset()
		return
	}
	if glob.Match(sectionPattern(w.dir, section), w.full) {
		w.store.Set(name, value)
	}
}
QUIRE_EOF

cat > internal/resolve/section.go <<'QUIRE_EOF'
package resolve

import (
	"strings"

	"quire/internal/glob"
)

// sectionPattern builds the glob a file path is matched against for a
// section header found in the EditorConfig file in dir:
//
//	no '/' in the header      dir + "**/" + header
//	'/' first                 dir + header
//	'/' elsewhere             dir + "/" + header
//
// The directory part is escaped so it only matches itself.
func sectionPattern(dir, header string) string {
	base := glob.EscapeDir(dir)
	switch {
	case !strings.Contains(header, "/"):
		return base + "**/" + header
	case header[0] == '/':
		return base + header
	default:
		return base + "/" + header
	}
}
QUIRE_EOF

cat > internal/version/version.go <<'QUIRE_EOF'
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

// Compare returns -1, 0 or +1 comparing v with o component by component.
func (v Version) Compare(o Version) int {
	for _, d := range [3][2]int{{v.Major, o.Major}, {v.Minor, o.Minor}, {v.Patch, o.Patch}} {
		if d[0] > d[1] {
			return 1
		}
		if d[0] < d[1] {
			return -1
		}
	}
	return 0
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
QUIRE_EOF

gofmt -l . | (! grep .)
go vet ./...
go build ./cmd/quire
