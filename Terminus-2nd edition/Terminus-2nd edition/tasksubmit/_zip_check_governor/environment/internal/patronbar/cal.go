package patronbar

import "github.com/terminus/holdfairctl/internal/model"

// IsSuspended reports whether patron is blocked on reconcileDate.
func IsSuspended(patronID, reconcileDate string, windows []model.Suspension) bool {
    for _, w := range windows {
        if w.PatronID != patronID {
            continue
        }
        if reconcileDate >= w.StartDate && reconcileDate < w.EndDate {
            return true
        }
    }
    return false
}
