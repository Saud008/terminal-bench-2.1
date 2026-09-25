package span

import (
	"sort"

	"github.com/terminus/brat-consensus-exporter/internal/model"
)

func overlaps(a, b model.StagedSpan) bool {
	return a.DocID == b.DocID && a.Label == b.Label && a.Start < b.End && b.Start < a.End
}

func spanLen(s model.StagedSpan) int {
	return s.End - s.Start
}

func ResolveOverlaps(spans []model.StagedSpan) []model.StagedSpan {
	if len(spans) == 0 {
		return nil
	}
	sorted := append([]model.StagedSpan(nil), spans...)
	sort.Slice(sorted, func(i, j int) bool {
		if sorted[i].DocID != sorted[j].DocID {
			return sorted[i].DocID < sorted[j].DocID
		}
		if sorted[i].Label != sorted[j].Label {
			return sorted[i].Label < sorted[j].Label
		}
		return spanLen(sorted[i]) < spanLen(sorted[j])
	})
	var groups [][]model.StagedSpan
	for _, s := range sorted {
		placed := false
		for gi := range groups {
			overlap := false
			for _, g := range groups[gi] {
				if overlaps(g, s) {
					overlap = true
					break
				}
			}
			if overlap {
				groups[gi] = append(groups[gi], s)
				placed = true
				break
			}
		}
		if !placed {
			groups = append(groups, []model.StagedSpan{s})
		}
	}
	var out []model.StagedSpan
	for _, g := range groups {
		winner := g[0]
		for _, c := range g[1:] {
			if spanLen(c) < spanLen(winner) {
				winner = c
			}
		}
		out = append(out, winner)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].DocID != out[j].DocID {
			return out[i].DocID < out[j].DocID
		}
		if out[i].Start != out[j].Start {
			return out[i].Start < out[j].Start
		}
		return out[i].End < out[j].End
	})
	return out
}
