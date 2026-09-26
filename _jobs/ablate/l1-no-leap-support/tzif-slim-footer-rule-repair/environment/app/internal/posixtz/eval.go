package posixtz

import "shiftclock/internal/civil"

// yearTransitions returns the start and end transitions for year y.
func (tz *TZ) yearTransitions(y int64) (start, end Transition) {
	start = Transition{At: tz.Start.Instant(y, tz.StdOffset), Zone: tz.dstZone()}
	end = Transition{At: tz.End.Instant(y, tz.StdOffset), Zone: tz.stdZone()}
	return start, end
}

// Lookup returns the local time type in effect at Unix time t.
func (tz *TZ) Lookup(t int64) Zone {
	if !tz.HasDST {
		return tz.stdZone()
	}
	start, end := tz.yearTransitions(civil.YearOf(t + tz.StdOffset))
	if t >= start.At && t < end.At {
		return tz.dstZone()
	}
	return tz.stdZone()
}

// Transitions returns the rule transitions with from <= At < to.
func (tz *TZ) Transitions(from, to int64) []Transition {
	if !tz.HasDST || from >= to {
		return nil
	}
	var out []Transition
	for y := civil.YearOf(from); y <= civil.YearOf(to); y++ {
		start, end := tz.yearTransitions(y)
		for _, tr := range []Transition{start, end} {
			if tr.At >= from && tr.At < to {
				out = append(out, tr)
			}
		}
	}
	return out
}
