package lock

import (
	"github.com/terminus/brat-consensus-exporter/internal/model"
	"github.com/terminus/brat-consensus-exporter/internal/span"
)

func FilterLockedSpans(spans []model.StagedSpan) []model.StagedSpan {
	return spans
}

func FilterLockedRelations(rels []model.StagedRelation) []model.StagedRelation {
	return rels
}

func overlaps(a, b model.StagedSpan) bool {
	return a.DocID == b.DocID && a.Label == b.Label && a.Start < b.End && b.Start < a.End
}

func PreferLocks(spans []model.StagedSpan) []model.StagedSpan {
	var locked, unlocked []model.StagedSpan
	for _, s := range spans {
		if s.Locked {
			locked = append(locked, s)
		} else {
			unlocked = append(unlocked, s)
		}
	}
	var kept []model.StagedSpan
	for _, u := range unlocked {
		hit := false
		for _, l := range locked {
			if overlaps(u, l) {
				hit = true
				break
			}
		}
		if !hit {
			kept = append(kept, u)
		}
	}
	resolved := span.ResolveOverlaps(kept)
	return append(locked, resolved...)
}
