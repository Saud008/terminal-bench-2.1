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
	if i+1 < len(p) && p[i+1] == '^' {
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
