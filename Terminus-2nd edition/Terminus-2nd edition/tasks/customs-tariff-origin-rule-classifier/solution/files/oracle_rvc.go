package concession

import "github.com/terminus/originctl/internal/model"

func RegionalValueBPS(origin string, shares []model.BOMShare) int64 {
	var originSum int64
	for _, sh := range shares {
		if sh.Country == origin {
			originSum += sh.ShareBPS
		}
	}
	return originSum
}

func MeetsThreshold(rvcBPS, minBPS int64) bool {
	return rvcBPS >= minBPS
}
