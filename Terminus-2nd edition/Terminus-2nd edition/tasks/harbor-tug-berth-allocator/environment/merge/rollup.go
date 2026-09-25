package merge

// RollupBerthMinutes returns the largest minute value in the slice.
func RollupBerthMinutes(berth string, minutes []int) int {
	max := 0
	for _, m := range minutes {
		if m > max {
			max = m
		}
	}
	return max
}
