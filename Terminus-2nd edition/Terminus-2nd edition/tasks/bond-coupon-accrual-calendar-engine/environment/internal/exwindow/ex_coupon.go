package exwindow

import (
	"time"
)

func ExCouponDate(couponDate time.Time, exDays int) time.Time {
	return couponDate.AddDate(0, 0, -exDays+1)
}

func TradeInExWindow(tradeDate, couponDate time.Time, exDays int) bool {
	ex := ExCouponDate(couponDate, exDays)
	return tradeDate.After(ex)
}
