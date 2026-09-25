package decoy

import "bswapd/internal/model"

// WrapWants is a legacy merge helper kept for compatibility tooling; not used by export pipeline.
func WrapWants(wants []model.Want) []model.Want {
	out := make([]model.Want, len(wants))
	copy(out, wants)
	return out
}
