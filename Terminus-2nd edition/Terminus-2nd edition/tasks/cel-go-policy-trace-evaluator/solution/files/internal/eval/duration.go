package duration

import (
	"fmt"
	"strconv"
	"strings"
)

func ParseDuration(s string) (int64, error) {
	s = strings.TrimSpace(s)
	if s == "" {
		return 0, fmt.Errorf("empty duration")
	}
	unit := s[len(s)-1]
	numStr := s[:len(s)-1]
	switch unit {
	case 's':
		if strings.HasSuffix(numStr, "m") {
			ms := strings.TrimSuffix(numStr, "m")
			v, err := strconv.ParseFloat(ms, 64)
			if err != nil {
				return 0, err
			}
			return int64(v * 1_000_000), nil
		}
		v, err := strconv.ParseFloat(numStr, 64)
		if err != nil {
			return 0, err
		}
		return int64(v * 1_000_000_000), nil
	case 'm':
		v, err := strconv.ParseFloat(numStr, 64)
		if err != nil {
			return 0, err
		}
		return int64(v * 60 * 1_000_000_000), nil
	default:
		return 0, fmt.Errorf("unsupported duration %q", s)
	}
}

func toNanos(v any) (int64, error) {
	switch t := v.(type) {
	case string:
		return ParseDuration(t)
	case int:
		return int64(t), nil
	case int64:
		return t, nil
	case float64:
		return int64(t), nil
	default:
		return 0, fmt.Errorf("unsupported duration value %T", v)
	}
}

func Compare(left any, right any) (int, error) {
	ln, err := toNanos(left)
	if err != nil {
		return 0, err
	}
	rn, err := toNanos(right)
	if err != nil {
		return 0, err
	}
	if ln < rn {
		return -1, nil
	}
	if ln > rn {
		return 1, nil
	}
	return 0, nil
}
