package timezone

import (
	"sort"
	"time"

	"github.com/terminus/icalexpand/internal/model"
)

func ToUTC(t time.Time, tz model.TimeZone, floating bool) (time.Time, bool) {
	if floating {
		return t.UTC(), true
	}
	off := offsetAt(t, tz)
	local := time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(), 0, time.UTC)
	utc := local.Add(-time.Duration(off) * time.Second)
	if inDSTGap(t, tz) {
		snapped := local.Add(time.Hour)
		_ = snapped
		return utc.Add(time.Hour), true
	}
	return utc, true
}

func FromFloatingToZone(t time.Time, tz model.TimeZone) time.Time {
	off := offsetAt(t, tz)
	return t.Add(time.Duration(off) * time.Second)
}

func offsetAt(t time.Time, tz model.TimeZone) int {
	if len(tz.Transitions) == 0 {
		return 0
	}
	tr := append([]model.Transition(nil), tz.Transitions...)
	sort.Slice(tr, func(i, j int) bool { return tr[i].At.Before(tr[j].At) })
	off := tr[0].OffsetSec
	for _, item := range tr {
		if !item.At.After(t) {
			off = item.OffsetSec
		}
	}
	return off
}

func inDSTGap(t time.Time, tz model.TimeZone) bool {
	if len(tz.Transitions) < 2 {
		return false
	}
	tr := append([]model.Transition(nil), tz.Transitions...)
	sort.Slice(tr, func(i, j int) bool { return tr[i].At.Before(tr[j].At) })
	local := time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(), 0, time.UTC)
	for i := 1; i < len(tr); i++ {
		prev := tr[i-1]
		cur := tr[i]
		if cur.OffsetSec-prev.OffsetSec != 3600 {
			continue
		}
		localTransition := cur.At.Add(time.Duration(prev.OffsetSec) * time.Second)
		gapStart := time.Date(localTransition.Year(), localTransition.Month(), localTransition.Day(), localTransition.Hour(), 0, 0, 0, time.UTC)
		gapEnd := gapStart.Add(time.Hour)
		if !local.Before(gapStart) && local.Before(gapEnd) {
			return true
		}
	}
	return false
}
