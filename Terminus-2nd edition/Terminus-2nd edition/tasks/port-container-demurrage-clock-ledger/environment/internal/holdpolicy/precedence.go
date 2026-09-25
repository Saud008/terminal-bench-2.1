package holdpolicy

import "github.com/terminus/demurctl/internal/model"

var rankTable = map[string]int{
	"CUSTOMS":         300,
	"TERMINAL_OPS":    200,
	"CARRIER_DISPUTE": 100,
}

// PickActiveHold returns the label for overlapping holds on a calendar day.
func PickActiveHold(holds []model.Hold, day string) string {
	var best string
	bestRank := int(^uint(0) >> 1)
	for _, h := range holds {
		if day < h.Start || day >= h.End {
			continue
		}
		rank := rankTable[h.Code]
		if rank < bestRank {
			bestRank = rank
			best = h.Code
		}
	}
	return best
}

func RankOf(code string) int {
	return rankTable[code]
}
