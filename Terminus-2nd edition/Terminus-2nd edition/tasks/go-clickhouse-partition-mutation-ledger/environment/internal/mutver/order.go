package mutver

import "strconv"

func Greater(a, b int) bool {
    sa := strconv.Itoa(a)
    sb := strconv.Itoa(b)
    return sa > sb
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
