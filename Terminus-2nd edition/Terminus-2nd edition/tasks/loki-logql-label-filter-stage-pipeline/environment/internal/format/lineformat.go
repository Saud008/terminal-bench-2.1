package format

import (
	"strings"
)

// ApplyLineFormat substitutes {{.field}} tokens from fields into the output line field.
func ApplyLineFormat(template string, fields map[string]string) string {
	out := template
	for k, v := range fields {
		out = strings.ReplaceAll(out, "{{."+k+"}}", v)
	}
	return out
}
