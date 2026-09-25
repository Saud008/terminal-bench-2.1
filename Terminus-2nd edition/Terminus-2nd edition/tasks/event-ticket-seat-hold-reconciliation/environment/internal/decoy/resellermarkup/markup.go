package resellermarkup

// ResellerMarkup is a decoy helper not used on reconcile hot path.
func ResellerMarkup(faceValueCents int, markupBps int) int {
    return faceValueCents + (faceValueCents * markupBps / 10000)
}
