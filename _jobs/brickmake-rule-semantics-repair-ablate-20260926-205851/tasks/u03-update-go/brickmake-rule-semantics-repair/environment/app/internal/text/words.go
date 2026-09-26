// Package text holds the word and pattern helpers shared by the
// expander, the parser and the rule engine.
package text

import "strings"

func isSpace(r rune) bool {
	switch r {
	case ' ', '\t', '\n', '\r', '\v', '\f':
		return true
	}
	return false
}

// Fields splits s into whitespace-separated words.
func Fields(s string) []string { return strings.FieldsFunc(s, isSpace) }

// Join joins words with single spaces.
func Join(words []string) string { return strings.Join(words, " ") }

// TrimSpace removes leading and trailing whitespace.
func TrimSpace(s string) string { return strings.TrimFunc(s, isSpace) }

// TrimLeft removes leading whitespace.
func TrimLeft(s string) string { return strings.TrimLeftFunc(s, isSpace) }

// IsBlank reports whether c is a space or a tab.
func IsBlank(c byte) bool { return c == ' ' || c == '\t' }

// Pattern is a word with at most one '%' wildcard.
type Pattern struct {
	Prefix, Suffix string
	Wild           bool
}

// ParsePattern splits p at its first '%'.
func ParsePattern(p string) Pattern {
	i := strings.IndexByte(p, '%')
	if i < 0 {
		return Pattern{Prefix: p}
	}
	return Pattern{Prefix: p[:i], Suffix: p[i+1:], Wild: true}
}

// Match returns the stem matched by '%'. A pattern without '%' matches
// only the identical word, with an empty stem. The stem may be empty.
func (p Pattern) Match(s string) (string, bool) {
	if !p.Wild {
		return "", s == p.Prefix
	}
	if len(s) < len(p.Prefix)+len(p.Suffix) {
		return "", false
	}
	if !strings.HasPrefix(s, p.Prefix) || !strings.HasSuffix(s, p.Suffix) {
		return "", false
	}
	return s[len(p.Prefix) : len(s)-len(p.Suffix)], true
}

// Match is ParsePattern(pattern).Match(s).
func Match(pattern, s string) (string, bool) { return ParsePattern(pattern).Match(s) }

// Subst replaces the first '%' of repl with stem. Without '%', repl is
// returned unchanged.
func Subst(repl, stem string) string {
	i := strings.IndexByte(repl, '%')
	if i < 0 {
		return repl
	}
	return repl[:i] + stem + repl[i+1:]
}

// Patsubst implements $(patsubst pattern,replacement,text).
func Patsubst(pattern, repl, s string) string {
	pat := ParsePattern(pattern)
	words := Fields(s)
	for i, w := range words {
		stem, ok := pat.Match(w)
		if !ok {
			continue
		}
		if pat.Wild {
			words[i] = Subst(repl, stem)
		} else {
			words[i] = repl
		}
	}
	return Join(words)
}

// SplitDir splits a file name after its last slash.
func SplitDir(name string) (dir, file string) {
	i := strings.LastIndexByte(name, '/')
	if i < 0 {
		return "", name
	}
	return name[:i+1], name[i+1:]
}

// Dir implements $(dir word).
func Dir(w string) string {
	d, _ := SplitDir(w)
	if d == "" {
		return "./"
	}
	return d
}

// Notdir implements $(notdir word).
func Notdir(w string) string {
	_, f := SplitDir(w)
	return f
}

// Suffix returns the suffix of the last path component, or "".
func Suffix(w string) string {
	_, f := SplitDir(w)
	i := strings.LastIndexByte(f, '.')
	if i < 0 {
		return ""
	}
	return f[i:]
}

// Basename removes the suffix of the last path component.
func Basename(w string) string {
	s := Suffix(w)
	return w[:len(w)-len(s)]
}

// SplitOrder splits prerequisite words at the first "|" word; the words
// after it are order-only.
func SplitOrder(words []string) (normal, orderOnly []string) {
	for i, w := range words {
		if w == "|" {
			for _, r := range words[i+1:] {
				if r != "|" {
					orderOnly = append(orderOnly, r)
				}
			}
			return words[:i], orderOnly
		}
	}
	return words, nil
}

// Uniq keeps the first occurrence of every word.
func Uniq(words []string) []string {
	seen := make(map[string]bool, len(words))
	out := words[:0:0]
	for _, w := range words {
		if !seen[w] {
			seen[w] = true
			out = append(out, w)
		}
	}
	return out
}
