package export

func SumWeighted(final map[string]int, weights map[string]int) int {
	total := 0
	for r, v := range final {
		w := weights[r]
		if w <= 0 {
			w = 1
		}
		total += v * w
	}
	return total
}
