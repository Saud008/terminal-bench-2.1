package format

import (
	"strings"
)

// ApplyLineFormat substitutes {{.field}} tokens from fields into the output line field.
func ApplyLineFormat(template string, fields map[string]string) string {
	norm := map[string]string{}
	for k, v := range fields {
		norm[k] = unescape(v)
	}
	out := template
	for k, v := range norm {
		out = strings.ReplaceAll(out, "{{."+k+"}}", v)
	}
	return out
}

func unescape(s string) string {
	var b strings.Builder
	i := 0
	for i < len(s) {
		if s[i] == '\\' && i+1 < len(s) {
			switch s[i+1] {
			case 'n':
				b.WriteByte('\n')
				i += 2
				continue
			case 't':
				b.WriteByte('\t')
				i += 2
				continue
			case 'r':
				b.WriteByte('\r')
				i += 2
				continue
			case '"':
				b.WriteByte('"')
				i += 2
				continue
			case '\\':
				b.WriteByte('\\')
				i += 2
				continue
			}
		}
		b.WriteByte(s[i])
		i++
	}
	return b.String()
}
