package holdexpire

import "github.com/terminus/venuetixctl/internal/model"

// IsActive reports whether hold is still active at eventClock.
func IsActive(h model.SeatHold, eventClock string) bool {
    if h.Status != "active" {
        return false
    }
    return eventClock < h.ExpiresAt
}
