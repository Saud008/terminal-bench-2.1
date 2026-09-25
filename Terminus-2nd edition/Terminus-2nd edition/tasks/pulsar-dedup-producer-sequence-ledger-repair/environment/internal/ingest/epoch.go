package ingest

// AllowSequenceReset permits lowering sequence when epoch is unchanged.
func AllowSequenceReset(newSeq, highWater int64, newEpoch, oldEpoch int) bool {
	if newSeq >= highWater {
		return true
	}
	return newEpoch == oldEpoch
}
