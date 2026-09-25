package apply

import "strings"

// SplitStatements splits SQL on semicolons outside single-quoted string literals.
func SplitStatements(sql string) []string {
	var out []string
	var cur strings.Builder
	inQuote := false
	for i := 0; i < len(sql); i++ {
		ch := sql[i]
		if ch == '\'' {
			inQuote = !inQuote
			cur.WriteByte(ch)
			continue
		}
		if ch == ';' && !inQuote {
			stmt := strings.TrimSpace(cur.String())
			if stmt != "" {
				out = append(out, stmt)
			}
			cur.Reset()
			continue
		}
		cur.WriteByte(ch)
	}
	stmt := strings.TrimSpace(cur.String())
	if stmt != "" {
		out = append(out, stmt)
	}
	return out
}
