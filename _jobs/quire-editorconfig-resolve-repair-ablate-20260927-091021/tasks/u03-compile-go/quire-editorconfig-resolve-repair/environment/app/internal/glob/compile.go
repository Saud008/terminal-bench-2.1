// Package glob matches file paths against EditorConfig section globs by
// translating each glob into an anchored regular expression.
package glob

import (
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
			b.add(`\/`, 2)
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
