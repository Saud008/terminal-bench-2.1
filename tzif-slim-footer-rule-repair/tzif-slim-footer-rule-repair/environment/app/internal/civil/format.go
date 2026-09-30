package civil

import (
	"fmt"
	"strconv"
	"strings"
)

const SecondsPerDay = 86400

// Split breaks a Unix time into a day number and the seconds into that day.
func Split(t int64) (days, sod int64) {
	days = FloorDiv(t, SecondsPerDay)
	return days, t - days*SecondsPerDay
}

// YearOf returns the calendar year containing Unix time t (read as UTC).
func YearOf(t int64) int64 {
	days, _ := Split(t)
	y, _, _ := CivilFromDays(days)
	return y
}

// Format renders t as YYYY-MM-DDTHH:MM:SS with no zone designator.
func Format(t int64) string {
	days, sod := Split(t)
	y, m, d := CivilFromDays(days)
	return fmt.Sprintf("%04d-%02d-%02dT%02d:%02d:%02d", y, m, d, sod/3600, sod/60%60, sod%60)
}

// FormatUTC renders t as an RFC 3339 UTC timestamp.
func FormatUTC(t int64) string {
	return Format(t) + "Z"
}

// ParseInstant accepts either a decimal Unix time or YYYY-MM-DDTHH:MM:SSZ.
func ParseInstant(s string) (int64, error) {
	if n, err := strconv.ParseInt(s, 10, 64); err == nil {
		return n, nil
	}
	if !strings.HasSuffix(s, "Z") || len(s) != 20 || s[4] != '-' || s[7] != '-' || s[10] != 'T' || s[13] != ':' || s[16] != ':' {
		return 0, fmt.Errorf("instant %q: want Unix seconds or YYYY-MM-DDTHH:MM:SSZ", s)
	}
	var fields [6]int64
	for i, span := range [6][2]int{{0, 4}, {5, 7}, {8, 10}, {11, 13}, {14, 16}, {17, 19}} {
		n, err := strconv.ParseInt(s[span[0]:span[1]], 10, 64)
		if err != nil {
			return 0, fmt.Errorf("instant %q: %v", s, err)
		}
		fields[i] = n
	}
	y, mo, d := fields[0], int(fields[1]), int(fields[2])
	if mo < 1 || mo > 12 || d < 1 || d > DaysInMonth(y, mo) || fields[3] > 23 || fields[4] > 59 || fields[5] > 59 {
		return 0, fmt.Errorf("instant %q: field out of range", s)
	}
	return DaysFromCivil(y, mo, d)*SecondsPerDay + fields[3]*3600 + fields[4]*60 + fields[5], nil
}
