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

	var best *candidate
	for _, acc := range accepts {
		if acc.Q <= 0 {
			continue
		}
		for li, lang := range langs {
			if lang.Q <= 0 {
				continue
			}
			for vi, v := range variants {
				if !negotiate.MediaTypeMatch(acc.Value, v.MediaType) {
					continue
				}
				if lang.Value != "*" && lang.Value != v.Language {
					continue
				}
				c := candidate{
					variant: v,
					meta: negotiate.RankedCandidate{
						Score:     acc.Q * lang.Q,
						AcceptPos: acc.Pos + li,
						Spec:      negotiate.MediaTypeSpecificity(acc.Value),
						LangExact: negotiate.LanguageExactness(lang.Value, v.Language),
						VariantIx: vi,
					},
				}
				if best == nil || c.meta.Score > best.meta.Score {
					best = &c
				}
			}
		}
	}
	if best == nil {
		v := variants[0]
		return &model.SelectedVariant{
			Variant:   v,
			MediaType: v.MediaType,
			Charset:   v.Charset,
			Language:  v.Language,
		}, true
	}
	v := best.variant
	return &model.SelectedVariant{
		Variant:   v,
		MediaType: v.MediaType,
		Charset:   v.Charset,
		Language:  v.Language,
	}, true
}
