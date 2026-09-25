package policycheck

import "github.com/terminus/ttalloc/internal/model"

func LabRoomOK(sec model.Section, room model.Room) bool {
    if !sec.RequiresLab {
        return true
    }
    return room.RoomKind == "lab"
}
