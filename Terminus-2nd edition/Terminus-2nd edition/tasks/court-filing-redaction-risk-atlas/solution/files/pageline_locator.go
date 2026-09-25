package provenance

import "github.com/terminus/filingatlas/internal/model"

func LocateLine(page model.Page, needle string) (pageNum int, lineNum int) {
    for _, ln := range page.Lines {
        if ln.Text != "" && containsFold(ln.Text, needle) {
            return page.PageNum, ln.LineNum
        }
    }
    return page.PageNum, 0
}

func containsFold(hay, needle string) bool {
    return len(needle) > 0 && indexOfFold(hay, needle) >= 0
}

func indexOfFold(hay, needle string) int {
    h := []rune(toLower(hay))
    n := []rune(toLower(needle))
    if len(n) == 0 || len(h) < len(n) {
        return -1
    }
    for i := 0; i+len(n) <= len(h); i++ {
        match := true
        for j := 0; j < len(n); j++ {
            if h[i+j] != n[j] {
                match = false
                break
            }
        }
        if match {
            return i
        }
    }
    return -1
}

func toLower(s string) string {
    b := []byte(s)
    for i, c := range b {
        if c >= 'A' && c <= 'Z' {
            b[i] = c + ('a' - 'A')
        }
    }
    return string(b)
}
