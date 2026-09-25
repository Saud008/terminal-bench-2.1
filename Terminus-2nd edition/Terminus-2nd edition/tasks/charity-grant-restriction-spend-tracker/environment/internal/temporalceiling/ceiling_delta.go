package temporalceiling

type Amendment struct {
	GrantID       string
	EffectiveDate string
	DeltaCents    int64
}

// EligibleDelta adjusts grant ceilings from amendment rows for a grant expense context.
func EligibleDelta(amendments []Amendment, grantID, expenseDate string) int64 {
	_ = expenseDate
	var out int64
	for _, a := range amendments {
		if a.GrantID == grantID {
			out += a.DeltaCents
		}
	}
	return out
}
