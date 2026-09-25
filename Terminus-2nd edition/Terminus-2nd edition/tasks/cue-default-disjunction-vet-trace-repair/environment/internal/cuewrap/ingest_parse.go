package cuewrap

// Ingest phase: parse workspace manifests and included CUE files before compose.

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

func LoadWorkspace(dir string) (*Workspace, error) {
	name := filepath.Base(dir)
	manifestPath := filepath.Join(dir, "workspace.cue")
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return nil, err
	}
	includes, err := parseManifest(string(data))
	if err != nil {
		return nil, err
	}
	ws := &Workspace{
		Dir:      dir,
		Name:     name,
		Includes: includes,
		Schemas:  map[string]SchemaSpec{},
		Configs:  map[string]ConfigSpec{},
	}
	for _, rel := range includes {
		path := filepath.Join(dir, rel)
		raw, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		if err := parseFile(ws, rel, string(raw)); err != nil {
			return nil, fmt.Errorf("%s: %w", rel, err)
		}
	}
	return ws, nil
}

func parseManifest(text string) ([]string, error) {
	lines := splitLines(text)
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "include") {
			start := strings.Index(line, "[")
			end := strings.Index(line, "]")
			if start < 0 || end < 0 {
				return nil, fmt.Errorf("invalid include line")
			}
			inner := line[start+1 : end]
			parts := strings.Split(inner, ",")
			out := make([]string, 0, len(parts))
			for _, p := range parts {
				p = strings.TrimSpace(p)
				p = strings.Trim(p, "\"")
				if p != "" {
					out = append(out, p)
				}
			}
			return out, nil
		}
	}
	return nil, fmt.Errorf("workspace include missing")
}

func parseFile(ws *Workspace, file string, text string) error {
	lines := splitLines(text)
	i := 0
	for i < len(lines) {
		lineNum := i + 1
		line := strings.TrimSpace(lines[i])
		i++
		if line == "" || strings.HasPrefix(line, "//") {
			continue
		}
		if strings.HasPrefix(line, "schema ") {
			spec, consumed, err := parseSchema(lines, i-1, file)
			if err != nil {
				return err
			}
			ws.Schemas[spec.Name] = spec
			i = consumed
			continue
		}
		if strings.HasPrefix(line, "config ") {
			spec, consumed, err := parseConfig(lines, i-1, file)
			if err != nil {
				return err
			}
			ws.Configs[spec.ID] = spec
			i = consumed
			continue
		}
		if strings.HasPrefix(line, "vet ") {
			parts := strings.Fields(line)
			if len(parts) != 3 {
				return fmt.Errorf("line %d: invalid vet rule", lineNum)
			}
			ws.VetRules = append(ws.VetRules, VetRule{
				Path: parts[1],
				Attr: parts[2],
				File: file,
				Line: lineNum,
			})
			continue
		}
		if strings.HasPrefix(line, "export ") {
			parts := strings.Fields(line)
			if len(parts) != 3 {
				return fmt.Errorf("line %d: invalid export rule", lineNum)
			}
			ws.Exports = append(ws.Exports, ExportRule{
				Path: parts[1],
				Kind: parts[2],
				File: file,
				Line: lineNum,
			})
			continue
		}
		return fmt.Errorf("line %d: unknown statement", lineNum)
	}
	return nil
}

func parseSchema(lines []string, start int, file string) (SchemaSpec, int, error) {
	line := strings.TrimSpace(lines[start])
	open := strings.Index(line, "{")
	if open < 0 {
		return SchemaSpec{}, start + 1, fmt.Errorf("schema missing body")
	}
	header := strings.TrimSpace(line[:open])
	parts := strings.Fields(header)
	if len(parts) != 2 {
		return SchemaSpec{}, start + 1, fmt.Errorf("invalid schema header")
	}
	spec := SchemaSpec{Name: parts[1], Fields: []FieldSpec{}, File: file, Line: start + 1}
	i := start
	if !strings.HasSuffix(line, "}") {
		i++
		for i < len(lines) {
			bodyLine := strings.TrimSpace(lines[i])
			i++
			if bodyLine == "}" {
				break
			}
			if bodyLine == "closed" {
				spec.Closed = true
				continue
			}
			if strings.HasPrefix(bodyLine, "embed ") {
				spec.Embed = strings.TrimSpace(strings.TrimPrefix(bodyLine, "embed"))
				continue
			}
			field, err := parseFieldDecl(bodyLine)
			if err != nil {
				return SchemaSpec{}, i, err
			}
			spec.Fields = append(spec.Fields, field)
		}
	}
	return spec, i, nil
}

func parseConfig(lines []string, start int, file string) (ConfigSpec, int, error) {
	line := strings.TrimSpace(lines[start])
	open := strings.Index(line, "{")
	if open < 0 {
		return ConfigSpec{}, start + 1, fmt.Errorf("config missing body")
	}
	header := strings.TrimSpace(strings.TrimSuffix(line[:open], "{"))
	if !strings.HasPrefix(header, "config ") {
		return ConfigSpec{}, start + 1, fmt.Errorf("invalid config header")
	}
	rest := strings.TrimSpace(strings.TrimPrefix(header, "config "))
	col := strings.Index(rest, ":")
	if col < 0 {
		return ConfigSpec{}, start + 1, fmt.Errorf("invalid config header")
	}
	spec := ConfigSpec{
		ID:     strings.TrimSpace(rest[:col]),
		Schema: strings.TrimSpace(rest[col+1:]),
		Fields: map[string]ConfigValue{},
		File:   file,
		Line:   start + 1,
	}

	i := start
	if !strings.HasSuffix(strings.TrimSpace(line), "}") {
		i++
		for i < len(lines) {
			bodyLine := strings.TrimSpace(lines[i])
			lineNum := i + 1
			i++
			if bodyLine == "}" {
				break
			}
			parts := strings.Fields(bodyLine)
			if len(parts) < 2 {
				return ConfigSpec{}, i, fmt.Errorf("invalid config field")
			}
			name := parts[0]
			val := ConfigValue{File: file, Line: lineNum}
			if parts[1] == "disjunct" {
				val.UseDisjunct = true
			} else {
				val.Literal = unquote(strings.Join(parts[1:], " "))
			}
			spec.Fields[name] = val
			spec.FieldOrder = append(spec.FieldOrder, name)
		}
	}
	return spec, i, nil
}

func parseFieldDecl(line string) (FieldSpec, error) {
	parts := strings.Fields(line)
	if len(parts) < 2 {
		return FieldSpec{}, fmt.Errorf("invalid field %q", line)
	}
	name := parts[0]
	optional := strings.HasSuffix(name, "?")
	if optional {
		name = strings.TrimSuffix(name, "?")
	}
	typ := parts[1]
	spec := FieldSpec{Name: name, Optional: optional}
	switch typ {
	case "string":
		spec.Type = TypeString
	case "int":
		spec.Type = TypeInt
	case "disjunct":
		spec.Type = TypeDisjunct
		spec.Disjuncts = parts[2:]
	default:
		return FieldSpec{}, fmt.Errorf("unknown type %s", typ)
	}
	return spec, nil
}

func splitLines(text string) []string {
	return strings.Split(strings.ReplaceAll(text, "\r\n", "\n"), "\n")
}

func unquote(s string) string {
	if len(s) >= 2 && ((s[0] == '"' && s[len(s)-1] == '"') || (s[0] == '\'' && s[len(s)-1] == '\'')) {
		return s[1 : len(s)-1]
	}
	return s
}

func ParseLiteralInt(s string) (int, error) {
	return strconv.Atoi(s)
}
