package model

type Bond struct {
	ISIN         string  `json:"isin"`
	FaceCents    int64   `json:"face_cents"`
	CouponBPS    int     `json:"coupon_bps"`
	Frequency    int     `json:"frequency"`
	DayCount     string  `json:"day_count"`
	ExDays       int     `json:"ex_days"`
	CalendarID   string  `json:"calendar_id"`
	IssueDate    string  `json:"issue_date"`
	MaturityDate string  `json:"maturity_date"`
}

type Trade struct {
	TradeID   string `json:"trade_id"`
	ISIN      string `json:"isin"`
	TradeDate string `json:"trade_date"`
	SettleLag int    `json:"settle_lag_bdays"`
}

type Calendar struct {
	ID       string   `json:"calendar_id"`
	Holidays []string `json:"holidays"`
}

type AccrualRow struct {
	TradeID        string `json:"trade_id"`
	ISIN           string `json:"isin"`
	PeriodStart    string `json:"period_start"`
	PeriodEnd      string `json:"period_end"`
	SettlementDate string `json:"settlement_date"`
	AccruedCents   int64  `json:"accrued_cents"`
	ExCoupon       bool   `json:"ex_coupon"`
}
