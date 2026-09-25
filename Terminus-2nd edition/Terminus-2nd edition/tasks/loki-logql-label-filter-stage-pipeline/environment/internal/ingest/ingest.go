package ingest

import (
	"bufio"
	"encoding/json"
	"os"
	"sort"
	"strings"

	"github.com/terminus/lokilogql/internal/types"
)

func LoadLines(path string) ([]types.LogLine, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var lines []types.LogLine
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var row types.LogLine
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return nil, err
		}
		lines = append(lines, row)
	}
	return lines, sc.Err()
}

func ParseQuery(raw string) (types.QueryAST, error) {
	raw = strings.TrimSpace(raw)
	parts := splitStages(raw)
	ast := types.QueryAST{Raw: raw, Stages: []types.QueryStage{}}
	for _, part := range parts {
		part = strings.TrimSpace(part)
		switch {
		case strings.HasPrefix(part, "{"):
			sel, err := parseSelector(part)
			if err != nil {
				return ast, err
			}
			ast.Stages = append(ast.Stages, types.QueryStage{Kind: "matcher", Selector: sel})
		case part == "json":
			ast.Stages = append(ast.Stages, types.QueryStage{Kind: "json"})
		case strings.HasPrefix(part, "line_format "):
			tpl := strings.TrimSpace(strings.TrimPrefix(part, "line_format "))
			tpl = strings.Trim(tpl, "\"")
			ast.Stages = append(ast.Stages, types.QueryStage{Kind: "line_format", Template: tpl})
		case strings.HasPrefix(part, "unwrap "):
			field := strings.TrimSpace(strings.TrimPrefix(part, "unwrap "))
			ast.Stages = append(ast.Stages, types.QueryStage{Kind: "unwrap", Field: field})
		case strings.HasPrefix(part, "sum by"):
			inner := strings.TrimSuffix(strings.TrimPrefix(part, "sum by"), ")")
			inner = strings.TrimPrefix(inner, "(")
			inner = strings.TrimSpace(inner)
			var group []string
			if inner != "" {
				for _, g := range strings.Split(inner, ",") {
					group = append(group, strings.TrimSpace(g))
				}
			}
			ast.Stages = append(ast.Stages, types.QueryStage{Kind: "sum_by", GroupBy: group})
		default:
			return ast, os.ErrInvalid
		}
	}
	ast.Canonical = canonicalize(ast)
	return ast, nil
}

func splitStages(raw string) []string {
	var parts []string
	depth := 0
	start := 0
	for i, ch := range raw {
		if ch == '{' {
			depth++
		}
		if ch == '}' {
			depth--
		}
		if ch == '|' && depth == 0 {
			parts = append(parts, raw[start:i])
			start = i + 1
		}
	}
	parts = append(parts, raw[start:])
	return parts
}

func parseSelector(part string) (map[string]string, error) {
	part = strings.Trim(part, "{}")
	sel := map[string]string{}
	if strings.TrimSpace(part) == "" {
		return sel, nil
	}
	for _, kv := range strings.Split(part, ",") {
		kv = strings.TrimSpace(kv)
		eq := strings.Index(kv, "=")
		if eq < 0 {
			return nil, os.ErrInvalid
		}
		key := strings.TrimSpace(kv[:eq])
		val := strings.Trim(strings.TrimSpace(kv[eq+1:]), "\"")
		sel[key] = val
	}
	return sel, nil
}

func canonicalize(ast types.QueryAST) string {
	var b strings.Builder
	for i, st := range ast.Stages {
		if i > 0 {
			b.WriteString(" | ")
		}
		switch st.Kind {
		case "matcher":
			keys := make([]string, 0, len(st.Selector))
			for k := range st.Selector {
				keys = append(keys, k)
			}
			sort.Strings(keys)
			b.WriteString("{")
			for j, k := range keys {
				if j > 0 {
					b.WriteString(",")
				}
				b.WriteString(k)
				b.WriteString("=\"")
				b.WriteString(st.Selector[k])
				b.WriteString("\"")
			}
			b.WriteString("}")
		case "json":
			b.WriteString("json")
		case "line_format":
			b.WriteString("line_format \"")
			b.WriteString(st.Template)
			b.WriteString("\"")
		case "unwrap":
			b.WriteString("unwrap ")
			b.WriteString(st.Field)
		case "sum_by":
			b.WriteString("sum by (")
			b.WriteString(strings.Join(st.GroupBy, ","))
			b.WriteString(")")
		}
	}
	return b.String()
}
