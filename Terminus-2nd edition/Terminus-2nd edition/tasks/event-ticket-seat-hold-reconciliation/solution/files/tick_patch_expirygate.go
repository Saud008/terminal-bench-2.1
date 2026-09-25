package holdexpire

import "github.com/terminus/venuetixctl/internal/model"

func IsActive(h model.SeatHold, eventClock string) bool {
    if h.Status != "active" {
        return false
    }
    return eventClock <= h.ExpiresAt
}
