package negotiate

import (
	"sort"

	"github.com/terminus/variantgate/internal/model"
)

type candidate struct {
	variant   model.Variant
	acceptQ   float64
	acceptPos int
	spec      int
	langExact int
	variantIx int
}

func Select(variants []model.Variant, in model.NegotiationInput) (*model.SelectedVariant, bool) {
	if len(variants) == 0 {
		return nil, false
	}
	accepts := ParseList(in.Accept)
	if len(accepts) == 0 {
		accepts = []Entry{{Value: "*/*", Q: 1.0, Pos: 0}}
	}
	sort.Slice(accepts, func(i, j int) bool {
		if accepts[i].Q == accepts[j].Q {
			return accepts[i].Pos > accepts[j].Pos
		}
		return accepts[i].Q < accepts[j].Q
	})

	langs := ParseList(in.AcceptLanguage)
	if len(langs) == 0 {
		langs = []Entry{{Value: "*", Q: 1.0, Pos: 0}}
	}
	sort.Slice(langs, func(i, j int) bool {
		if langs[i].Q == langs[j].Q {
			return langs[i].Pos > langs[j].Pos
		}
		return langs[i].Q < langs[j].Q
	})

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
				if !MediaTypeMatch(acc.Value, v.MediaType) {
					continue
				}
				if lang.Value != "*" && lang.Value != v.Language {
					continue
				}
				c := candidate{
					variant:   v,
					acceptQ:   acc.Q * lang.Q,
					acceptPos: acc.Pos + li,
					spec:      MediaTypeSpecificity(acc.Value),
					langExact: LanguageExactness(lang.Value, v.Language),
					variantIx: vi,
				}
				if best == nil || c.acceptQ > best.acceptQ {
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
