package ical

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/terminus/icalexpand/internal/model"
)

func LoadCalendar(path string) ([]model.Event, map[string]model.TimeZone, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, nil, err
	}
	lines := unfold(string(data))
	var zones = map[string]model.TimeZone{}
	var events []model.Event
	var curTZ model.TimeZone
	var tzStd, tzDst int
	var tzToDst, tzToStd time.Time
	var inTZ, inEvent bool
	var ev model.Event
	for _, line := range lines {
		switch {
		case line == "BEGIN:VTIMEZONE":
			inTZ = true
			curTZ = model.TimeZone{}
			tzStd, tzDst = 0, 0
		case line == "END:VTIMEZONE":
			if curTZ.TZID != "" {
				if !tzToDst.IsZero() && !tzToStd.IsZero() {
					curTZ.Transitions = []model.Transition{
						{At: time.Date(1970, 1, 1, 0, 0, 0, 0, time.UTC), OffsetSec: tzStd},
						{At: tzToDst, OffsetSec: tzDst},
						{At: tzToStd, OffsetSec: tzStd},
					}
				}
				zones[curTZ.TZID] = curTZ
			}
			inTZ = false
		case inTZ && strings.HasPrefix(line, "TZID:"):
			curTZ.TZID = strings.TrimPrefix(line, "TZID:")
		case inTZ && strings.HasPrefix(line, "X-OFFSET-STANDARD:"):
			tzStd, _ = strconv.Atoi(strings.TrimPrefix(line, "X-OFFSET-STANDARD:"))
		case inTZ && strings.HasPrefix(line, "X-OFFSET-DAYLIGHT:"):
			tzDst, _ = strconv.Atoi(strings.TrimPrefix(line, "X-OFFSET-DAYLIGHT:"))
		case inTZ && strings.HasPrefix(line, "X-TRANSITION-TO-DST:"):
			tzToDst, _ = parseICSDate(strings.TrimPrefix(line, "X-TRANSITION-TO-DST:"))
		case inTZ && strings.HasPrefix(line, "X-TRANSITION-TO-STD:"):
			tzToStd, _ = parseICSDate(strings.TrimPrefix(line, "X-TRANSITION-TO-STD:"))
		case line == "BEGIN:VEVENT":
			inEvent = true
			ev = model.Event{}
		case line == "END:VEVENT":
			events = append(events, ev)
			inEvent = false
		case inEvent && strings.HasPrefix(line, "UID:"):
			ev.UID = strings.TrimPrefix(line, "UID:")
		case inEvent && strings.HasPrefix(line, "DTSTART"):
			val := propertyValue(line)
			if strings.Contains(line, ";TZID=") {
				parts := strings.Split(line, ";TZID=")
				ev.TZID = strings.Split(parts[1], ":")[0]
				ev.Floating = false
			} else if strings.HasSuffix(val, "Z") {
				ev.Floating = false
			} else {
				ev.Floating = true
			}
			t, err := parseICSDate(val)
			if err != nil {
				return nil, nil, fmt.Errorf("invalid DTSTART: %w", err)
			}
			ev.DTStart = t
		case inEvent && strings.HasPrefix(line, "RRULE:"):
			rule, err := parseRRule(strings.TrimPrefix(line, "RRULE:"))
			if err != nil {
				return nil, nil, err
			}
			ev.RRule = rule
		case inEvent && strings.HasPrefix(line, "EXDATE"):
			for _, part := range strings.Split(propertyValue(line), ",") {
				t, err := parseICSDate(strings.TrimSpace(part))
				if err != nil {
					return nil, nil, err
				}
				ev.EXDates = append(ev.EXDates, t)
			}
		case inEvent && strings.HasPrefix(line, "RDATE"):
			for _, part := range strings.Split(propertyValue(line), ",") {
				t, err := parseICSDate(strings.TrimSpace(part))
				if err != nil {
					return nil, nil, err
				}
				ev.RDates = append(ev.RDates, t)
			}
		}
	}
	return events, zones, nil
}

func unfold(text string) []string {
	var out []string
	var cur string
	sc := bufio.NewScanner(strings.NewReader(text))
	for sc.Scan() {
		line := sc.Text()
		if strings.HasPrefix(line, " ") || strings.HasPrefix(line, "\t") {
			cur += strings.TrimLeft(line, " \t")
		} else {
			if cur != "" {
				out = append(out, cur)
			}
			cur = line
		}
	}
	if cur != "" {
		out = append(out, cur)
	}
	return out
}

func propertyValue(line string) string {
	idx := strings.Index(line, ":")
	if idx < 0 {
		return ""
	}
	return line[idx+1:]
}

func propertyParam(line, key string) string {
	parts := strings.Split(line, ";")
	for _, p := range parts {
		if strings.HasPrefix(p, key+":") {
			return strings.TrimPrefix(p, key+":")
		}
	}
	return ""
}

func parseOffset(raw string) int {
	raw = strings.TrimSpace(raw)
	sign := 1
	if strings.HasPrefix(raw, "-") {
		sign = -1
		raw = strings.TrimPrefix(raw, "-")
	}
	if len(raw) != 4 {
		return 0
	}
	h := atoi(raw[:2])
	m := atoi(raw[2:])
	return sign * (h*3600 + m*60)
}

func atoi(s string) int {
	n := 0
	for _, ch := range s {
		if ch < '0' || ch > '9' {
			continue
		}
		n = n*10 + int(ch-'0')
	}
	return n
}

func parseICSDate(raw string) (time.Time, error) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return time.Time{}, fmt.Errorf("empty date")
	}
	if strings.HasSuffix(raw, "Z") {
		return time.Parse("20060102T150405Z", raw)
	}
	return time.Parse("20060102T150405", raw)
}

func parseRRule(raw string) (model.RRule, error) {
	r := model.RRule{Interval: 1}
	for _, part := range strings.Split(raw, ";") {
		kv := strings.SplitN(part, "=", 2)
		if len(kv) != 2 {
			continue
		}
		switch kv[0] {
		case "FREQ":
			r.Freq = kv[1]
		case "INTERVAL":
			r.Interval = atoi(kv[1])
		case "BYDAY":
			r.ByDay = strings.Split(kv[1], ",")
		case "BYSETPOS":
			n, _ := strconv.Atoi(kv[1])
			r.BySetPos = n
		case "COUNT":
			r.Count = atoi(kv[1])
		case "UNTIL":
			u, err := parseICSDate(kv[1])
			if err != nil {
				return r, err
			}
			r.Until = &u
			r.UntilUTC = strings.HasSuffix(kv[1], "Z")
		}
	}
	return r, nil
}
