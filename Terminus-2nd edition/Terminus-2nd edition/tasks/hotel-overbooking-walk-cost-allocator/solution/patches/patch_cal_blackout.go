package blackoutcal

import "github.com/terminus/overbookctl/internal/model"

// RoomBlocked reports whether room is unavailable on nightDate.
func RoomBlocked(roomID, nightDate string, windows []model.Maintenance) bool {
    for _, w := range windows {
        if w.RoomID != roomID {
            continue
        }
        if windowCoversDate(w, nightDate) {
            return true
        }
    }
    return false
}
