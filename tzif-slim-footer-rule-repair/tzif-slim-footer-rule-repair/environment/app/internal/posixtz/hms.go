package posixtz

import (
	"fmt"
	"strconv"
	"strings"
)

// parseHMS parses [+-]hh[:mm[:ss]] into seconds. maxHour bounds the hour
// field; signed controls whether a leading sign is accepted.
func parseHMS(s string, maxHour int, signed bool) (int64, error) {
	neg := false
	if signed && s != "" && (s[0] == '+' || s[0] == '-') {
		neg = s[0] == '-'
		s = s[1:]
	}
	parts := strings.Split(s, ":")
	if s == "" || len(parts) > 3 {
		return 0, fmt.Errorf("malformed %q", s)
	}
	var total int64
	for i, part := range parts {
		if part == "" || len(part) > 3 || (i > 0 && len(part) != 2) {
			return 0, fmt.Errorf("malformed %q", s)
		}
		n, err := strconv.Atoi(part)
		if err != nil {
			return 0, fmt.Errorf("malformed %q", s)
		}
		switch i {
		case 0:
			if n > maxHour {
				return 0, fmt.Errorf("hour %d out of range", n)
			}
			total += int64(n) * 3600
		default:
			if n > 59 {
				return 0, fmt.Errorf("field %d out of range", n)
			}
			if i == 1 {
				total += int64(n) * 60
			} else {
				total += int64(n)
			}
		}
	}
	if neg {
		total = -total
	}
	return total, nil
}

// parseRuleTime parses the "/time" part of a rule. RFC 8536 section 3.3.1
// extends POSIX here: the hour may be signed and range from -167 to 167.
func parseRuleTime(s string) (int64, error) {
	return parseHMS(s, 167, true)
}
