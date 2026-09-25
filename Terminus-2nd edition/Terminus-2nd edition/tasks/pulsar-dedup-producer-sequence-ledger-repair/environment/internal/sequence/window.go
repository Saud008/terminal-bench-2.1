package sequence

// WithinWindow reports whether seq is inside the dedup window of highWater.
func WithinWindow(seq, highWater int64, window int) bool {
	if seq >= highWater {
		return true
	}
	return highWater-seq <= int64(window)
}

// AcceptOutOfOrder returns true when an out-of-order sequence may advance the ledger.
func AcceptOutOfOrder(seq, highWater int64, window int, seenSeq map[int64]struct{}) bool {
	if !WithinWindow(seq, highWater, window) {
		return false
	}
	return true
}
