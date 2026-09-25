package mutver

func Greater(a, b int) bool {
    return a > b
}

func MaxVersion(versions []int) int {
    best := versions[0]
    for _, v := range versions[1:] {
        if Greater(v, best) {
            best = v
        }
    }
    return best
}
