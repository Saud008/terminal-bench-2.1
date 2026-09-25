package accrue

import (
	"time"

	"github.com/terminus/bondacc/internal/daycount"
	"github.com/terminus/bondacc/internal/exwindow"
	"github.com/terminus/bondacc/internal/model"
	"github.com/terminus/bondacc/internal/schedule"
)

func ComputeRow(bond model.Bond, trade model.Trade, holidays map[string]struct{}, issue time.Time, couponDates []time.Time) model.AccrualRow {
	tradeDt := schedule.Parse(trade.TradeDate)
	settle := tradeDt
	periodStart, periodEnd := schedule.PeriodContaining(settle, issue, couponDates)
	yf := daycount.YearFraction(periodStart, settle, bond.DayCount)
	accrued := daycount.AccruedCents(bond.FaceCents, bond.CouponBPS, yf)
	ex := exwindow.TradeInExWindow(tradeDt, periodEnd, bond.ExDays)
	if ex {
		accrued = 0
	}
	return model.AccrualRow{
		TradeID:        trade.TradeID,
		ISIN:           bond.ISIN,
		PeriodStart:    periodStart.Format("2006-01-02"),
		PeriodEnd:      periodEnd.Format("2006-01-02"),
		SettlementDate: settle.Format("2006-01-02"),
		AccruedCents:   accrued,
		ExCoupon:       ex,
	}
}
