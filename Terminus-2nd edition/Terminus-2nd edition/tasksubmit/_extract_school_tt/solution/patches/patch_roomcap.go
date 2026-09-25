package policycheck

import "github.com/terminus/ttalloc/internal/model"

func RoomHasCapacity(room model.Room, slotID string, sec model.Section, usage map[string]int, margin int) bool {
    key := room.RoomID + "|" + slotID
    total := usage[key] + sec.Enrolled
    limit := room.Capacity - margin
    return total <= limit
}

func AddUsage(room model.Room, slotID string, sec model.Section, usage map[string]int) {
    key := room.RoomID + "|" + slotID
    usage[key] = usage[key] + sec.Enrolled
}
