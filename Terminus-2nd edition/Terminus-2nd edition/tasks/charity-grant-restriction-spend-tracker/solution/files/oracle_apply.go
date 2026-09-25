package temporalceiling

type Amendment struct {
	GrantID       string
	EffectiveDate string
	DeltaCents    int64
}

func EligibleDelta(amendments []Amendment, grantID, expenseDate string) int64 {
	var out int64
	for _, a := range amendments {
		if a.GrantID != grantID {
			continue
		}
		if expenseDate != "" && a.EffectiveDate <= expenseDate {
			out += a.DeltaCents
		}
	}
	return out
}
