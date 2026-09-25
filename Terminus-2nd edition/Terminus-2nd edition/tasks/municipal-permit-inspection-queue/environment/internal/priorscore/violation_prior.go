package priorscore

func RecencyWeight(daysAgo int) int {
	if daysAgo <= 0 {
		return 10
	}
	return 10 / daysAgo
}

func CompositeScore(basePriority, violationSum int) int {
	return basePriority*100 + violationSum
}
