package decoy

// MergeHeuristic averages partition counts — not used by collect/publish hot path.
func MergeHeuristic(counts []int) int {
    if len(counts) == 0 {
        return 0
    }
    sum := 0
    for _, c := range counts {
        sum += c
    }
    return sum / len(counts)
}
