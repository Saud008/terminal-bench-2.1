package tzif

import (
	"sort"

	"shiftclock/internal/posixtz"
)

func (f *File) zone(i uint8) posixtz.Zone {
	lt := f.Types[i]
	return posixtz.Zone{Offset: lt.Offset, Abbr: lt.Abbr, IsDST: lt.IsDST}
}

// Lookup returns the local time type in effect at Unix time t.
//
// Before the first transition the first ttinfo applies. After the last
// transition (or everywhere, for a file without transitions) the footer
// rule applies when there is one; otherwise the last transition's type
// stays in effect.
func (f *File) Lookup(t int64) posixtz.Zone {
	n := len(f.Times)
	if n == 0 {
		if f.Rule != nil {
			return f.Rule.Lookup(t)
		}
		return f.zone(0)
	}
	if t < f.Times[0] {
		return f.zone(0)
	}
	if t > f.Times[n-1] && f.Rule != nil {
		return f.Rule.Lookup(t)
	}
	i := sort.Search(n, func(i int) bool { return f.Times[i] > t }) - 1
	return f.zone(f.Indices[i])
}

// Transitions lists the changes of local time type with from <= At < to,
// taken from the transition table and, past its end, from the footer.
// Entries that would not change the offset, abbreviation or DST flag are
// dropped.
func (f *File) Transitions(from, to int64) []posixtz.Transition {
	var all []posixtz.Transition
	for i, at := range f.Times {
		all = append(all, posixtz.Transition{At: at, Zone: f.zone(f.Indices[i])})
	}
	if f.Rule != nil {
		ruleFrom := from
		if n := len(f.Times); n > 0 && f.Times[n-1]+1 > ruleFrom {
			ruleFrom = f.Times[n-1] + 1
		}
		all = append(all, f.Rule.Transitions(ruleFrom, to)...)
	}

	var out []posixtz.Transition
	for _, tr := range all {
		if tr.At >= to {
			break
		}
		if tr.Zone == f.Lookup(tr.At-1) {
			continue
		}
		if tr.At >= from {
			out = append(out, tr)
		}
	}
	return out
}
