package model

type Reading struct {
	TsUTC string  `json:"ts_utc"`
	MWh   float64 `json:"mwh"`
}

type Meter struct {
	MeterID  string    `json:"meter_id"`
	Readings []Reading `json:"readings"`
}

type Curtailment struct {
	StartUTC string `json:"start_utc"`
	EndUTC   string `json:"end_utc"`
}

type MarketPrice struct {
	IntervalStartUTC string `json:"interval_start_utc"`
	PriceCents       int64  `json:"price_cents"`
}

type Scenario struct {
	ScenarioID       string          `json:"scenario_id"`
	PPAID            string          `json:"ppa_id"`
	PeriodStart      string          `json:"period_start"`
	PeriodEnd        string          `json:"period_end"`
	StrikePriceCents int64           `json:"strike_price_cents"`
	IntervalMinutes  int             `json:"interval_minutes"`
	Holidays         []string        `json:"holidays"`
	Meters           []Meter         `json:"meters"`
	Curtailments     []Curtailment   `json:"curtailments"`
	MarketPrices     []MarketPrice   `json:"market_prices"`
}

type SettlementLine struct {
	MeterID          string  `json:"meter_id"`
	IntervalStartUTC string  `json:"interval_start_utc"`
	MWh              float64 `json:"mwh"`
	StrikeCents      int64   `json:"strike_cents"`
	MarketCents      int64   `json:"market_cents"`
	SettlementCents  int64   `json:"settlement_cents"`
	AmountCents      int64   `json:"amount_cents"`
	SkippedCurtail   bool    `json:"skipped_curtail"`
}

type InvoiceRollup struct {
	ScenarioID      string `json:"scenario_id"`
	PPAID           string `json:"ppa_id"`
	PeriodStart     string `json:"period_start"`
	PeriodEnd       string `json:"period_end"`
	BillingDays     int    `json:"billing_days"`
	LineCount       int    `json:"line_count"`
	TotalAmountCents int64 `json:"total_amount_cents"`
	LinesDigest     string `json:"lines_digest"`
}
