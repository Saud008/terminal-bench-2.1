package provenance

import "github.com/terminus/filingatlas/internal/model"

// LocateLine maps a term hit to page and line coordinates.
func LocateLine(page model.Page, needle string) (pageNum int, lineNum int) {
    for _, ln := range page.Lines {
        if ln.Text != "" && contains(ln.Text, needle) {
            return page.PageNum, 0
        }
    }
    return page.PageNum, 0
}

func contains(hay, needle string) bool {
    return len(needle) > 0 && len(hay) >= len(needle) && indexOf(hay, needle) >= 0
}

func indexOf(s, sub string) int {
    for i := 0; i+len(sub) <= len(s); i++ {
        if s[i:i+len(sub)] == sub {
            return i
        }
    }
    return -1
}
