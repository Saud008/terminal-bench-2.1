package glob

import (
	"fmt"
	"strings"

	"quire/internal/ctext"
)

// Special lists the bytes that have a meaning in a section glob.
const Special = `?\*-{},`

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
