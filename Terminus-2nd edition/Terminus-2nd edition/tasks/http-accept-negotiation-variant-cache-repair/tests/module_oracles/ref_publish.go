package staging

import (
	"github.com/terminus/variantgate/internal/model"
	"github.com/terminus/variantgate/internal/negotiate"
)

type candidate struct {
	variant model.Variant
	meta    negotiate.RankedCandidate
}

func SelectFromSnapshot(snap Snapshot, variants []model.Variant) (*model.SelectedVariant, bool) {
	if len(variants) == 0 {
		return nil, false
	}
	if err := VerifySnapshot(snap); err != nil {
		return nil, false
	}
	in := snap.Prepared
	accepts := negotiate.ParseList(in.Accept)
	if len(accepts) == 0 {
		accepts = []negotiate.Entry{{Value: "*/*", Q: 1.0, Pos: 0}}
	}
	negotiate.RankEntries(accepts)

	langs := negotiate.ParseList(in.AcceptLanguage)
	if len(langs) == 0 {
		langs = []negotiate.Entry{{Value: "*", Q: 1.0, Pos: 0}}
	}
	negotiate.RankEntries(langs)

	charsets := negotiate.ParseList(in.AcceptCharset)
	charsetOpen := len(charsets) == 0
	if !charsetOpen {
		negotiate.RankEntries(charsets)
	}

	var best *candidate
	for _, acc := range accepts {
		if acc.Q <= 0 {
			continue
		}
		for _, lang := range langs {
			if lang.Q <= 0 {
				continue
			}
			if charsetOpen {
				for vi, v := range variants {
					if !negotiate.MediaTypeMatch(acc.Value, v.MediaType) {
						continue
					}
					if !negotiate.LanguageMatch(lang.Value, v.Language) {
						continue
					}
					consider(&best, v, acc, lang, nil, vi)
				}
				continue
			}
			for _, cs := range charsets {
				if cs.Q <= 0 {
					continue
				}
				for vi, v := range variants {
					if !negotiate.MediaTypeMatch(acc.Value, v.MediaType) {
						continue
					}
					if !negotiate.LanguageMatch(lang.Value, v.Language) {
						continue
					}
					if !negotiate.CharsetMatch(cs.Value, v.Charset) {
						continue
					}
					consider(&best, v, acc, lang, &cs, vi)
				}
			}
		}
	}
	if best == nil {
		return nil, false
	}
	v := best.variant
	return &model.SelectedVariant{
		Variant:   v,
		MediaType: v.MediaType,
		Charset:   v.Charset,
		Language:  v.Language,
	}, true
}

func consider(best **candidate, v model.Variant, acc, lang negotiate.Entry, cs *negotiate.Entry, vi int) {
	score := acc.Q * lang.Q
	if cs != nil {
		score *= cs.Q
	}
	c := candidate{
		variant: v,
		meta: negotiate.RankedCandidate{
			Score:     score,
			AcceptPos: acc.Pos,
			Spec:      negotiate.MediaTypeSpecificity(acc.Value),
			LangExact: negotiate.LanguageExactness(lang.Value, v.Language),
			VariantIx: vi,
		},
	}
	if *best == nil || negotiate.BetterCandidate(c.meta, (*best).meta) {
		*best = &c
	}
}
