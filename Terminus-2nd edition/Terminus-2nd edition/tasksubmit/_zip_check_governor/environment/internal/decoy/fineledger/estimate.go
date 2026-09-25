package fineledger

// EstimateOverdueFine is a decoy helper not used on reconcile hot path.
func EstimateOverdueFine(daysLate int, dailyCents int) int {
    if daysLate <= 0 {
        return 0
    }
    return daysLate * dailyCents
}
