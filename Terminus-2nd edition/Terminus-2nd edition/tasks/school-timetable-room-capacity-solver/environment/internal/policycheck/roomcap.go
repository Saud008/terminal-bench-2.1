package policycheck

import "github.com/terminus/ttalloc/internal/model"

func RoomHasCapacity(room model.Room, slotID string, sec model.Section, usage map[string]int, margin int) bool {
    key := room.RoomID + "|" + slotID
    current := usage[key]
    if current > 0 {
        return false
    }
    limit := room.Capacity - margin
    return sec.Enrolled <= limit
}

func AddUsage(room model.Room, slotID string, sec model.Section, usage map[string]int) {
    key := room.RoomID + "|" + slotID
    usage[key] = sec.Enrolled
}
