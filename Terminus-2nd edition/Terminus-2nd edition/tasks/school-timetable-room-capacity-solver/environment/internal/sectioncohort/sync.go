package sectioncohort

import "github.com/terminus/ttalloc/internal/model"

func SlotForGroup(sec model.Section, assigned map[string]string) (string, bool) {
    key := sec.CourseID
    if key == "" {
        return "", false
    }
    slot, ok := assigned[key]
    return slot, ok
}

func RememberGroup(sec model.Section, slot string, assigned map[string]string) {
    assigned[sec.CourseID] = slot
}
