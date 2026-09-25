package trade

import (
	"time"

	"github.com/terminus/bondacc/internal/calendar"
)

func SettlementDate(tradeDate time.Time, lagBDays int, holidays map[string]struct{}) time.Time {
	return calendar.AddBusinessDays(tradeDate, lagBDays, holidays)
}
