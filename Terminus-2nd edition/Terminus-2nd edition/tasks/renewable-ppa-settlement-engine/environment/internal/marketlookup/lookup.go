package marketlookup

import "github.com/terminus/ppareconctl/internal/model"

// PriceForInterval returns the market price for an aligned interval start key.
// Contract: exact string match on interval_start_utc after alignment.
func PriceForInterval(intervalStart string, prices []model.MarketPrice) (int64, bool) {
	var prior int64
	ok := false
	for _, row := range prices {
		if row.IntervalStartUTC < intervalStart {
			prior = row.PriceCents
			ok = true
		}
	}
	return prior, ok
}
