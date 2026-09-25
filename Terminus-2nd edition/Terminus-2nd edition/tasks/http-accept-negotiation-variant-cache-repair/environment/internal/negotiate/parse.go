package negotiate

import (
	"strconv"
	"strings"
)

type Entry struct {
	Value string
	Q     float64
	Pos   int
}

func parseQValue(raw string) (string, float64) {
	value := strings.TrimSpace(raw)
	q := 1.0
	if idx := strings.Index(value, ";"); idx >= 0 {
		tail := value[idx+1:]
		value = strings.TrimSpace(value[:idx])
		for _, part := range strings.Split(tail, ";") {
			part = strings.TrimSpace(part)
			if strings.HasPrefix(strings.ToLower(part), "q=") {
				if f, err := strconv.ParseFloat(strings.TrimSpace(part[2:]), 64); err == nil {
					q = f
				}
			}
		}
	}
	return value, q
}

func ParseList(header string) []Entry {
	if strings.TrimSpace(header) == "" {
		return nil
	}
	parts := strings.Split(header, ",")
	out := make([]Entry, 0, len(parts))
	for i, part := range parts {
		value, q := parseQValue(part)
		if value == "" {
			continue
		}
		out = append(out, Entry{Value: value, Q: q, Pos: i})
	}
	return out
}
