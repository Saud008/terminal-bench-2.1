package replag

func Suppressed(lagMax, threshold int) bool {
    return lagMax >= threshold
}

func MaxLag(rows []int) int {
    best := 0
    for _, lag := range rows {
        if lag > best {
            best = lag
        }
    }
    return best
}
