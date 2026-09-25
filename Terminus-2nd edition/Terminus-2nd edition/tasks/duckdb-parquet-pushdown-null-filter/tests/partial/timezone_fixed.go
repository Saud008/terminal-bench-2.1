package timezone

import (
	"strings"
	"time"
)

func ParseBound(raw, catalogTZ string) (time.Time, error) {
	trimmed := strings.TrimSuffix(raw, "Z")
	layout := "2006-01-02T15:04:05"
	loc := time.UTC
	if catalogTZ != "" && !strings.EqualFold(catalogTZ, "UTC") {
		loc = time.Local
	}
	return time.ParseInLocation(layout, trimmed, loc)
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
	b = b.UTC()
	v = v.UTC()
	return !v.Before(b)
}
