package planrule

import "strings"

func DateActive(start, end, asOf string) bool {
    if asOf < start {
        return false
    }
    if end != "" && asOf > end {
        return false
    }
    return true
}

func TieBreakStart(a, b string) string {
    if strings.Compare(a, b) <= 0 {
        return a
    }
    return b
}
