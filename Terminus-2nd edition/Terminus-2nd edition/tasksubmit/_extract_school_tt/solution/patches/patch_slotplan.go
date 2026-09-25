package slotplan

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/ttalloc/internal/allocgate"
    "github.com/terminus/ttalloc/internal/model"
    "github.com/terminus/ttalloc/internal/policycheck"
    "github.com/terminus/ttalloc/internal/rankkey"
    "github.com/terminus/ttalloc/internal/sectioncohort"
)

func RunPlan(scenario string) error {
    bundle, err := readBundle()
    if err != nil {
        return err
    }
    teacherTaken := map[string]string{}
    roomUsage := map[string]int{}
    groupSlots := map[string]string{}
    var assignments []model.Assignment
    slots := bundle.Slots
    rooms := bundle.Rooms
    sort.SliceStable(slots, func(i, j int) bool { return slots[i].SlotID < slots[j].SlotID })
    sort.SliceStable(rooms, func(i, j int) bool { return rooms[i].RoomID < rooms[j].RoomID })
    sort.SliceStable(bundle.Sections, func(i, j int) bool { return bundle.Sections[i].SectionID < bundle.Sections[j].SectionID })
    for _, sec := range bundle.Sections {
        if slotID, ok := sectioncohort.SlotForGroup(sec, groupSlots); ok {
            slot := findSlot(slots, slotID)
            for _, room := range rooms {
                if !policycheck.LabRoomOK(sec, room) {
                    continue
                }
                if !policycheck.RoomHasCapacity(room, slotID, sec, roomUsage, bundle.Policies.CapacityMargin) {
                    continue
                }
                sc := rankkey.StableScore(sec, room, slot)
                assignments = append(assignments, model.Assignment{
                    SectionID: sec.SectionID, TeacherID: sec.TeacherID,
                    RoomID: room.RoomID, SlotID: slotID, Score: sc,
                })
                policycheck.AddUsage(room, slotID, sec, roomUsage)
                break
            }
            continue
        }
        placed := false
        for _, slot := range slots {
            if !policycheck.TeacherAvailable(sec, slot.SlotID, bundle.Teachers) {
                continue
            }
            if !policycheck.TeacherFree(sec.TeacherID, slot.SlotID, teacherTaken) {
                continue
            }
            for _, room := range rooms {
                if !policycheck.LabRoomOK(sec, room) {
                    continue
                }
                if !policycheck.RoomHasCapacity(room, slot.SlotID, sec, roomUsage, bundle.Policies.CapacityMargin) {
                    continue
                }
                sc := rankkey.StableScore(sec, room, slot)
                assignments = append(assignments, model.Assignment{
                    SectionID: sec.SectionID, TeacherID: sec.TeacherID,
                    RoomID: room.RoomID, SlotID: slot.SlotID, Score: sc,
                })
                teacherTaken[sec.TeacherID] = slot.SlotID
                policycheck.AddUsage(room, slot.SlotID, sec, roomUsage)
                sectioncohort.RememberGroup(sec, slot.SlotID, groupSlots)
                placed = true
                break
            }
            if placed {
                break
            }
        }
    }
    sort.SliceStable(assignments, func(i, j int) bool { return rankkey.Less(assignments[i], assignments[j]) })
    logBody := map[string]any{"scenario": scenario, "assignment_count": len(assignments), "assignments": assignments}
    raw, _ := json.MarshalIndent(logBody, "", "  ")
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    if err := os.WriteFile("/app/work/allocate-log.json", append(raw, '\n'), 0o644); err != nil {
        return err
    }
    return allocgate.BumpAllocationPass()
}

func findSlot(slots []model.Slot, slotID string) model.Slot {
    for _, slot := range slots {
        if slot.SlotID == slotID {
            return slot
        }
    }
    return model.Slot{SlotID: slotID}
}

func readBundle() (*model.RosterBundle, error) {
    raw, err := os.ReadFile("/app/state/active-roster.json")
    if err != nil {
        return nil, err
    }
    var bundle model.RosterBundle
    if err := json.Unmarshal(raw, &bundle); err != nil {
        return nil, err
    }
    return &bundle, nil
}
