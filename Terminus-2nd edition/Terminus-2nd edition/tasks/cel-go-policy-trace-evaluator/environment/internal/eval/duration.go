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

// Compare returns -1, 0, 1. Baseline compares raw left/right without full canonicalization when types differ.
func Compare(left any, right any) (int, error) {
	ls, lok := left.(string)
	rs, rok := right.(string)
	if lok && rok {
		ln, err := ParseDuration(ls)
		if err != nil {
			return 0, err
		}
		rn, err := ParseDuration(rs)
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
	li, liok := toInt64(left)
	ri, riok := toInt64(right)
	if liok && riok {
		if li < ri {
			return -1, nil
		}
		if li > ri {
			return 1, nil
		}
		return 0, nil
	}
	if lok && riok {
		return strings.Compare(ls, strconv.FormatInt(ri, 10)), nil
	}
	if liok && rok {
		return strings.Compare(strconv.FormatInt(li, 10), rs), nil
	}
	return 0, fmt.Errorf("incomparable duration operands")
}

func toInt64(v any) (int64, bool) {
	switch t := v.(type) {
	case int:
		return int64(t), true
	case int64:
		return t, true
	case float64:
		return int64(t), true
	default:
		return 0, false
	}
}
