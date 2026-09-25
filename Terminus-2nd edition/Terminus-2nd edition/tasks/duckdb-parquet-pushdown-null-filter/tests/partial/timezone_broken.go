package timezone

import (
	"strings"
	"time"
)

// ParseBound parses a timestamp predicate bound using catalog timezone rules.
func ParseBound(raw, catalogTZ string) (time.Time, error) {
	trimmed := strings.TrimSuffix(raw, "Z")
	layout := "2006-01-02T15:04:05"
	return time.ParseInLocation(layout, trimmed, time.Local)
}

func MeetsTsGte(value, bound string, catalogTZ string) bool {
	if bound == "" {
		return true
	}
	v, err := time.Parse(time.RFC3339, value)
	if err != nil {
		return false
	}
	b, err := ParseBound(bound, catalogTZ)
	if err != nil {
		return false
	}
	return !v.Before(b)
}
