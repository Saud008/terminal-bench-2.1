package decoy

// ReplayHeatmap rollup decoy — not referenced by wfhistctl hot path.
func HeatmapScore(eventKinds []string) int {
    n := 0
    for _, k := range eventKinds {
        n += len(k)
    }
    return n
}
