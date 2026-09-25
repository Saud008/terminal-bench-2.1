package metercarry

func CarryUnits(included, usage int) int {
    left := included - usage
    if left < 0 {
        return 0
    }
    return left
}

func OverageUnits(included, usage, carry int) int {
    billable := usage - included - carry
    if billable < 0 {
        return 0
    }
    return billable
}
