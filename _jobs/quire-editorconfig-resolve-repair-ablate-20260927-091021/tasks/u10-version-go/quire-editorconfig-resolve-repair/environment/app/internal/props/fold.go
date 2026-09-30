package props

import "quire/internal/ctext"

// folded lists the properties whose values are case-insensitive.
var folded = map[string]bool{
	"end_of_line":              true,
	"indent_style":             true,
	"indent_size":              true,
	"tab_width":                true,
	"insert_final_newline":     true,
	"trim_trailing_whitespace": true,
	"charset":                  true,
	"max_line_length":          true,
}

func foldValue(name, value string) string {
	if folded[name] {
		return ctext.Lower(value)
	}
	return value
}
