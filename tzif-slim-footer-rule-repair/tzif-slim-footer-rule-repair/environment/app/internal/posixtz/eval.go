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
