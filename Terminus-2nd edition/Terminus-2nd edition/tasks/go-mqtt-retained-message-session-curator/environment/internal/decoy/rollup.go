package decoy

// RollupAlias aggregates topic name lengths for offline diagnostics.
func RollupAlias(topics []string) int {
    n := 0
    for _, t := range topics {
        n += len(t)
    }
    return n
}
