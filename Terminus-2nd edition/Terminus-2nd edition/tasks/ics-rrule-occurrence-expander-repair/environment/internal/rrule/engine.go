package rrule

import (
	"sort"
	"time"

	"github.com/terminus/icalexpand/internal/model"
	"github.com/terminus/icalexpand/internal/timezone"
)

func ExpandEvent(ev model.Event, zones map[string]model.TimeZone, windowStart, windowEnd time.Time) []model.Occurrence {
	tz := zones[ev.TZID]
	series := expandSeries(ev, tz)
	series = limitCount(series, ev.RRule.Count)
	merged := mergeOccurrences(series, ev.EXDates, ev.RDates)
	var out []model.Occurrence
	for _, local := range merged {
		if !withinUntil(local, ev.RRule, ev.DTStart) {
			continue
		}
		utc, ok := timezone.ToUTC(local, tz, ev.Floating)
		if !ok {
			continue
		}
		if utc.Before(windowStart) || utc.After(windowEnd) {
			continue
		}
		out = append(out, model.Occurrence{UID: ev.UID, StartUTC: utc.UTC()})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].StartUTC.Before(out[j].StartUTC) })
	return out
}

func expandSeries(ev model.Event, tz model.TimeZone) []time.Time {
	switch ev.RRule.Freq {
	case "WEEKLY":
		return expandWeekly(ev)
	case "MONTHLY":
		return expandMonthly(ev)
	default:
		return []time.Time{ev.DTStart}
	}
}
