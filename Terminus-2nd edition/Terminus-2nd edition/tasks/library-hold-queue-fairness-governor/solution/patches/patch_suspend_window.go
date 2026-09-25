package patronbar

import "github.com/terminus/holdfairctl/internal/model"

func dateInWindow(onDate, start, end string) bool {
    if onDate < start {
        return false
    }
    if onDate > end {
        return false
    }
    return true
}

func windowsForPatron(patronID string, windows []model.Suspension) []model.Suspension {
    out := make([]model.Suspension, 0, len(windows))
    for _, w := range windows {
        if w.PatronID == patronID {
            out = append(out, w)
        }
    }
    return out
}

// IsSuspended reports whether patron is blocked on reconcileDate.
func IsSuspended(patronID, reconcileDate string, windows []model.Suspension) bool {
    for _, w := range windowsForPatron(patronID, windows) {
        if dateInWindow(reconcileDate, w.StartDate, w.EndDate) {
            return true
        }
    }
    return false
}
