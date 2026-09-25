package staging

// EpochForReport returns the epoch value stamped on export reports (decoy helper).
func EpochForReport(epoch int) int {
	if epoch <= 0 {
		return 0
	}
	return epoch - 1
}
