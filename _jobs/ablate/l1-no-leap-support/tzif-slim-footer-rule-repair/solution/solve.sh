#!/usr/bin/env bash
set -euo pipefail

cd /app

# Rule times: RFC 8536 3.3.1 lets the hour be signed and run to 167
# (America/Nuuk "/-1", Asia/Jerusalem "/26"); a bad value is an error, not 02:00.
cat > internal/posixtz/hms.go <<'EOF'
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
		if part == "" || len(part) > 3 || (i > 0 && len(part) != 2) || strings.Trim(part, "0123456789") != "" {
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
EOF

# Day selection: "Jn" never counts February 29, so from J60 on it shifts by one
# day in leap years; "Mm.5.d" is the last d of the month, not a fifth week.
cat > internal/posixtz/rule.go <<'EOF'
package posixtz

import "shiftclock/internal/civil"

// yearDay returns the zero-based day of year (0 = January 1) that r names in
// year y.
func (r Rule) yearDay(y int64) int {
	switch r.Kind {
	case JulianNoLeap:
		d := r.Day - 1
		if r.Day >= 60 && civil.IsLeap(y) {
			d++
		}
		return d
	case ZeroBased:
		return r.Day
	default:
		first := civil.DaysFromCivil(y, r.Month, 1)
		day := 1 + (r.Weekday-civil.Weekday(first)+7)%7 + (r.Week-1)*7
		if day > civil.DaysInMonth(y, r.Month) {
			day -= 7
		}
		return int(first - civil.DaysFromCivil(y, 1, 1) + int64(day-1))
	}
}

// Instant returns the UTC time of the transition r names in year y, given
// the UTC offset in effect just before the transition.
func (r Rule) Instant(y int64, before int64) int64 {
	days := civil.DaysFromCivil(y, 1, 1) + int64(r.yearDay(y))
	return days*civil.SecondsPerDay + r.Time - before
}
EOF

# Evaluation: the end rule is wall time under the DST offset, and DST may wrap
# the year (southern hemisphere, Europe/Dublin), so resolve t against the
# chronologically ordered transitions of the neighbouring years.
cat > internal/posixtz/eval.go <<'EOF'
package posixtz

import (
	"sort"

	"shiftclock/internal/civil"
)

// yearTransitions returns the two transitions whose rules fall in year y,
// in chronological order.
func (tz *TZ) yearTransitions(y int64) [2]Transition {
	start := Transition{At: tz.Start.Instant(y, tz.StdOffset), Zone: tz.dstZone()}
	end := Transition{At: tz.End.Instant(y, tz.DstOffset), Zone: tz.stdZone()}
	if end.At < start.At {
		return [2]Transition{end, start}
	}
	return [2]Transition{start, end}
}

// Lookup returns the local time type in effect at Unix time t.
func (tz *TZ) Lookup(t int64) Zone {
	if !tz.HasDST {
		return tz.stdZone()
	}
	y := civil.YearOf(t)
	var best Transition
	found := false
	for yy := y - 1; yy <= y+1; yy++ {
		for _, tr := range tz.yearTransitions(yy) {
			if tr.At <= t && (!found || tr.At > best.At) {
				best, found = tr, true
			}
		}
	}
	return best.Zone
}

// Transitions returns the rule transitions with from <= At < to, in order.
func (tz *TZ) Transitions(from, to int64) []Transition {
	if !tz.HasDST || from >= to {
		return nil
	}
	var out []Transition
	for y := civil.YearOf(from) - 1; y <= civil.YearOf(to)+1; y++ {
		for _, tr := range tz.yearTransitions(y) {
			if tr.At >= from && tr.At < to {
				out = append(out, tr)
			}
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].At < out[j].At })
	return out
}
EOF

test -z "$(gofmt -l internal cmd)"
go vet ./...
go build ./cmd/shiftclock
rm -f shiftclock
