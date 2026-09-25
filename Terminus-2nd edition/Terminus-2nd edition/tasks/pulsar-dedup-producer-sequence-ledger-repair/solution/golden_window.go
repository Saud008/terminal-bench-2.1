package sequence

func WithinWindow(seq, highWater int64, window int) bool {
	if seq >= highWater {
		return true
	}
	return highWater-seq <= int64(window)
}

func AcceptOutOfOrder(seq, highWater int64, window int, seenSeq map[int64]struct{}) bool {
	if !WithinWindow(seq, highWater, window) {
		return false
	}
	_, dup := seenSeq[seq]
	return !dup
}
