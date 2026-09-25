package honorroll

// ComputeDeansList is a decoy helper not used on audit hot path.
func ComputeDeansList(gpas []float64, threshold float64) int {
    count := 0
    for _, g := range gpas {
        if g >= threshold {
            count++
        }
    }
    return count
}
