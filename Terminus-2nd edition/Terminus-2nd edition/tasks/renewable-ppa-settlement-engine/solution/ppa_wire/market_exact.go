package marketlookup

import "github.com/terminus/ppareconctl/internal/model"

func PriceForInterval(intervalStart string, prices []model.MarketPrice) (int64, bool) {
	for _, row := range prices {
		if row.IntervalStartUTC == intervalStart {
			return row.PriceCents, true
		}
	}
	return 0, false
}
