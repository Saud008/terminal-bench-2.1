package parse

import (
	"fmt"
	"strconv"
	"strings"
	"unicode"

	"github.com/terminus/collectdctl/internal/model"
)

func ParseStream(content string) ([]model.RawReading, error) {
	var out []model.RawReading
	lines := strings.Split(content, "\n")
	for i, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		r, err := ParseLine(line)
		if err != nil {
			return nil, fmt.Errorf("line %d: %w", i+1, err)
		}
		r.LineNo = i + 1
		out = append(out, r)
	}
	return out, nil
}

func ParseLine(line string) (model.RawReading, error) {
	if !strings.HasPrefix(line, "PUTVAL ") {
		return model.RawReading{}, fmt.Errorf("bad putval")
	}
	rest := strings.TrimSpace(line[len("PUTVAL "):])
	identifier, tail, err := readIdentifier(rest)
	if err != nil {
		return model.RawReading{}, err
	}
	interval := int64(10)
	tail = strings.TrimSpace(tail)
	for strings.HasPrefix(tail, "interval=") {
		field, rem, _ := strings.Cut(tail, " ")
		val, err := strconv.ParseInt(strings.TrimPrefix(field, "interval="), 10, 64)
		if err != nil {
			return model.RawReading{}, fmt.Errorf("bad interval")
		}
		interval = val
		tail = strings.TrimSpace(rem)
	}
	groups, err := parseValueGroups(tail)
	if err != nil {
		return model.RawReading{}, err
	}
	return model.RawReading{Identifier: identifier, Interval: interval, Groups: groups}, nil
}

func readIdentifier(rest string) (string, string, error) {
	if rest == "" {
		return "", "", fmt.Errorf("missing identifier")
	}
	if rest[0] == '"' {
		var b strings.Builder
		escaped := false
		for i := 1; i < len(rest); i++ {
			ch := rest[i]
			if escaped {
				if ch == '/' {
					b.WriteByte('/')
				} else {
					b.WriteByte('\\')
					b.WriteByte(ch)
				}
				escaped = false
				continue
			}
			if ch == '\\' {
				escaped = true
				continue
			}
			if ch == '"' {
				return b.String(), strings.TrimSpace(rest[i+1:]), nil
			}
			b.WriteByte(ch)
		}
		return "", "", fmt.Errorf("bad quoted identifier")
	}
	end := 0
	for end < len(rest) && !unicode.IsSpace(rune(rest[end])) {
		end++
	}
	if end == 0 {
		return "", "", fmt.Errorf("missing identifier")
	}
	return rest[:end], rest[end:], nil
}

func parseValueGroups(rest string) ([]model.ValueGroup, error) {
	if strings.TrimSpace(rest) == "" {
		return nil, fmt.Errorf("missing values")
	}
	var groups []model.ValueGroup
	for _, part := range strings.Fields(rest) {
		fields := strings.Split(part, ":")
		if len(fields) < 2 {
			return nil, fmt.Errorf("bad values")
		}
		epoch, err := strconv.ParseInt(fields[0], 10, 64)
		if err != nil {
			return nil, fmt.Errorf("bad epoch")
		}
		vals := make([]float64, 0, len(fields)-1)
		for _, raw := range fields[1:] {
			v, err := strconv.ParseFloat(raw, 64)
			if err != nil {
				return nil, fmt.Errorf("bad value")
			}
			vals = append(vals, v)
		}
		groups = append(groups, model.ValueGroup{Epoch: epoch, Values: vals})
	}
	return groups, nil
}
