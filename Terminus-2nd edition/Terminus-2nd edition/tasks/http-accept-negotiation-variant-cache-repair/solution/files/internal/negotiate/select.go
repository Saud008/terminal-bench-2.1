package negotiate

import (
	"sort"

	"github.com/terminus/variantgate/internal/model"
)

type candidate struct {
	variant   model.Variant
	score     float64
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
	sort.SliceStable(accepts, func(i, j int) bool {
		if accepts[i].Q == accepts[j].Q {
			return accepts[i].Pos < accepts[j].Pos
		}
		return accepts[i].Q > accepts[j].Q
	})

	langs := ParseList(in.AcceptLanguage)
	if len(langs) == 0 {
		langs = []Entry{{Value: "*", Q: 1.0, Pos: 0}}
	}
	sort.SliceStable(langs, func(i, j int) bool {
		if langs[i].Q == langs[j].Q {
			return langs[i].Pos < langs[j].Pos
		}
		return langs[i].Q > langs[j].Q
	})

	charsets := ParseList(in.AcceptCharset)
	charsetOpen := len(charsets) == 0
	sort.SliceStable(charsets, func(i, j int) bool {
		if charsets[i].Q == charsets[j].Q {
			return charsets[i].Pos < charsets[j].Pos
		}
		return charsets[i].Q > charsets[j].Q
	})

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
					if !MediaTypeMatch(acc.Value, v.MediaType) {
						continue
					}
					if !LanguageMatch(lang.Value, v.Language) {
						continue
					}
					updateBest(&best, candidate{
						variant:   v,
						score:     acc.Q * lang.Q,
						acceptPos: acc.Pos,
						spec:      MediaTypeSpecificity(acc.Value),
						langExact: LanguageExactness(lang.Value, v.Language),
						variantIx: vi,
					})
				}
				continue
			}
			for _, cs := range charsets {
				if cs.Q <= 0 {
					continue
				}
				for vi, v := range variants {
					if !MediaTypeMatch(acc.Value, v.MediaType) {
						continue
					}
					if !LanguageMatch(lang.Value, v.Language) {
						continue
					}
					if !CharsetMatch(cs.Value, v.Charset) {
						continue
					}
					updateBest(&best, candidate{
						variant:   v,
						score:     acc.Q * lang.Q * cs.Q,
						acceptPos: acc.Pos,
						spec:      MediaTypeSpecificity(acc.Value),
						langExact: LanguageExactness(lang.Value, v.Language),
						variantIx: vi,
					})
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

func updateBest(best **candidate, c candidate) {
	if *best == nil {
		*best = &c
		return
	}
	cur := *best
	if c.score > cur.score {
		*best = &c
		return
	}
	if c.score < cur.score {
		return
	}
	if c.acceptPos < cur.acceptPos {
		*best = &c
		return
	}
	if c.acceptPos > cur.acceptPos {
		return
	}
	if c.spec > cur.spec {
		*best = &c
		return
	}
	if c.spec < cur.spec {
		return
	}
	if c.langExact > cur.langExact {
		*best = &c
		return
	}
	if c.langExact < cur.langExact {
		return
	}
	if c.variantIx < cur.variantIx {
		*best = &c
	}
}
