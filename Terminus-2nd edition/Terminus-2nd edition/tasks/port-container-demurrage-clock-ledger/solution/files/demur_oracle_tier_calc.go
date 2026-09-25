package tarifftier

import "github.com/terminus/demurctl/internal/model"

type TierBreakdown struct {
	Tier1Days  int
	Tier2Days  int
	Tier3Days  int
	TotalCents int
}

// ComputeTierCharges assigns demurrage days 1-3 to tier1, 4-7 tier2, 8+ tier3.
func ComputeTierCharges(demurrageDayCount int, tariff model.Tariff) TierBreakdown {
	var out TierBreakdown
	for day := 1; day <= demurrageDayCount; day++ {
		switch {
		case day <= 3:
			out.Tier1Days++
			out.TotalCents += tariff.Tier1RateCents
		case day <= 7:
			out.Tier2Days++
			out.TotalCents += tariff.Tier2RateCents
		default:
			out.Tier3Days++
			out.TotalCents += tariff.Tier3RateCents
		}
	}
	return out
}
