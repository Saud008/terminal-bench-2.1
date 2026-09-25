package metercarry

func CarryUnits(included, usage int) int {
	return 0
}

func OverageUnits(included, usage, carry int) int {
	billable := usage - included - carry
	if billable < 0 {
		return 0
	}
	return billable
}
