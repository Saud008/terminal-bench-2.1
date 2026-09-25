package strikemath

func SettlementPriceCents(strike, market int64) int64 {
	if strike < market {
		return strike
	}
	return market
}

func AmountCents(mwh float64, settlementCents int64) int64 {
	return int64(mwh*float64(settlementCents) + 0.5)
}
