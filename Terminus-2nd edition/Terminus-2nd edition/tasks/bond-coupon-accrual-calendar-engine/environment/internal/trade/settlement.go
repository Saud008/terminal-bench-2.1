package trade

import (
	"time"
)

func SettlementDate(tradeDate time.Time, lagBDays int, holidays map[string]struct{}) time.Time {
	return tradeDate.AddDate(0, 0, lagBDays)
}
