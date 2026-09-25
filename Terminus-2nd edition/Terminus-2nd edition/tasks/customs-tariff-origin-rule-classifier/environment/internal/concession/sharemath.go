package concession

import "github.com/terminus/originctl/internal/model"

// RegionalValueBPS sums originating share for declared origin country.
func RegionalValueBPS(origin string, shares []model.BOMShare) int64 {
	var foreign int64
	for _, sh := range shares {
		if sh.Country != origin {
			foreign += sh.ShareBPS
		}
	}
	return foreign
}

func MeetsThreshold(rvcBPS, minBPS int64) bool {
	return rvcBPS < minBPS
}
