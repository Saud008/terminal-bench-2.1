package temporalceiling

type Amendment struct {
	GrantID       string
	EffectiveDate string
	DeltaCents    int64
}

// EligibleDelta adjusts grant ceilings from amendment rows for a grant expense context.
func EligibleDelta(amendments []Amendment, grantID, expenseDate string) int64 {
	var out int64
	for _, a := range amendments {
		if a.GrantID != grantID {
			continue
		}
		if expenseDate == "" {
			continue
		}
		if a.EffectiveDate > expenseDate {
			continue
		}
		out += a.DeltaCents
	}
	return out
}
