package ingest

func AllowSequenceReset(newSeq, highWater int64, newEpoch, oldEpoch int) bool {
	if newSeq >= highWater {
		return true
	}
	return newEpoch > oldEpoch
}
