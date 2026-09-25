package eval

import (
	"fmt"
	"regexp"
	"strings"
)

type Expr struct {
	Left  string
	Op    string
	Right string
}

var allowLine = regexp.MustCompile(`allow\s*\{\s*(.+)\s*\}`)

func ParsePolicy(source string) (Expr, error) {
	lines := strings.Split(source, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "#") || line == "" {
			continue
		}
		m := allowLine.FindStringSubmatch(line)
		if len(m) == 2 {
			return parseExpr(strings.TrimSpace(m[1]))
		}
	}
	return Expr{}, fmt.Errorf("allow rule not found")
}

func parseExpr(s string) (Expr, error) {
	for _, op := range []string{">=", "<=", "!=", "==", ">", "<"} {
		if i := strings.Index(s, op); i > 0 {
			return Expr{
				Left:  strings.TrimSpace(s[:i]),
				Op:    op,
				Right: strings.TrimSpace(s[i+len(op):]),
			}, nil
		}
	}
	return Expr{}, fmt.Errorf("unsupported expr: %s", s)
}

func DataRefs(expr Expr) []string {
	var out []string
	for _, side := range []string{expr.Left, expr.Right} {
		if strings.HasPrefix(side, "data.") {
			out = append(out, side)
		}
	}
	return out
}
