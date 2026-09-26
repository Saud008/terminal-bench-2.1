package parse

import (
	"strings"

	"brickmake/internal/vars"
)

// oddBackslashes reports whether s ends in an odd number of backslashes,
// i.e. whether the newline after it is escaped.
func oddBackslashes(s string) bool {
	n := 0
	for i := len(s) - 1; i >= 0 && s[i] == '\\'; i-- {
		n++
	}
	return n%2 == 1
}

// hashAt reports whether the '#' at s[i] starts a comment and returns the
// number of backslashes immediately before it.
func hashAt(s string, i int) (bool, int) {
	n := 0
	for j := i - 1; j >= 0 && s[j] == '\\'; j-- {
		n++
	}
	return n%2 == 0, n
}

// stripComment removes a trailing comment. "\#" is a literal '#', and each
// pair of backslashes before a '#' stands for one backslash.
func stripComment(s string) string {
	for i := 0; i < len(s); i++ {
		if s[i] != '#' {
			continue
		}
		comment, n := hashAt(s, i)
		if comment {
			return s[:i-n] + strings.Repeat("\\", n/2)
		}
		s = s[:i-n] + strings.Repeat("\\", (n-1)/2) + s[i:]
		i = i - n + (n-1)/2
	}
	return s
}

// skipRef returns the index of the last byte of the variable reference
// that starts with the '$' at s[i].
func skipRef(s string, i int) int {
	if i+1 >= len(s) {
		return i
	}
	open := s[i+1]
	var close byte
	switch open {
	case '(':
		close = ')'
	case '{':
		close = '}'
	default:
		return i + 1
	}
	depth := 0
	for j := i + 2; j < len(s); j++ {
		switch s[j] {
		case open:
			depth++
		case close:
			if depth == 0 {
				return j
			}
			depth--
		}
	}
	return len(s) - 1
}

// findTop returns the index of the first c outside variable references.
func findTop(s string, c byte) int {
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '$':
			i = skipRef(s, i)
		case c:
			return i
		}
	}
	return -1
}

// splitRecipe splits a rule line at the first ';' outside variable
// references, or cuts a comment that comes first.
func splitRecipe(s string) (rule string, recipe *string) {
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '$':
			i = skipRef(s, i)
		case ';':
			r := s[i+1:]
			return s[:i], &r
		case '#':
			if comment, _ := hashAt(s, i); comment {
				return stripComment(s), nil
			}
		}
	}
	return stripComment(s), nil
}

// scanAssign recognizes a variable assignment. A ':' that is not part of
// ":=" or "::=" before any '=' makes the line a rule.
func scanAssign(s string) (name string, op vars.Op, value string, ok bool) {
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '$':
			i = skipRef(s, i)
		case '=':
			return strings.TrimRight(s[:i], " \t"), vars.OpRecursive, strings.TrimLeft(s[i+1:], " \t"), true
		case ':':
			if strings.HasPrefix(s[i:], ":=") {
				return strings.TrimRight(s[:i], " \t"), vars.OpSimple, strings.TrimLeft(s[i+2:], " \t"), true
			}
			if strings.HasPrefix(s[i:], "::=") {
				return strings.TrimRight(s[:i], " \t"), vars.OpSimple, strings.TrimLeft(s[i+3:], " \t"), true
			}
			return "", 0, "", false
		case '+', '?':
			if i+1 < len(s) && s[i+1] == '=' {
				op := vars.OpAppend
				if s[i] == '?' {
					op = vars.OpConditional
				}
				return strings.TrimRight(s[:i], " \t"), op, strings.TrimLeft(s[i+2:], " \t"), true
			}
		}
	}
	return "", 0, "", false
}

// ScanAssign is scanAssign for command-line variable definitions.
func ScanAssign(s string) (name string, op vars.Op, value string, ok bool) { return scanAssign(s) }
