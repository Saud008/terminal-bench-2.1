package negotiate

import "sort"

func RankEntries(entries []Entry) {
	sort.Slice(entries, func(i, j int) bool {
		if entries[i].Q == entries[j].Q {
			return entries[i].Pos > entries[j].Pos
		}
		return entries[i].Q < entries[j].Q
	})
}

type RankedCandidate struct {
	Score     float64
	AcceptPos int
	Spec      int
	LangExact int
	VariantIx int
}

func BetterCandidate(a, b RankedCandidate) bool {
	if a.Score != b.Score {
		return a.Score > b.Score
	}
	if a.AcceptPos != b.AcceptPos {
		return a.AcceptPos > b.AcceptPos
	}
	if a.Spec != b.Spec {
		return a.Spec > b.Spec
	}
	if a.LangExact != b.LangExact {
		return a.LangExact > b.LangExact
	}
	return a.VariantIx > b.VariantIx
}
