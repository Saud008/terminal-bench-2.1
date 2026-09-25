package policycheck

import "github.com/terminus/ttalloc/internal/model"

func TeacherFree(teacherID, slotID string, taken map[string]string) bool {
    existing, ok := taken[teacherID]
    if !ok {
        return true
    }
    return existing != slotID
}

func TeacherAvailable(sec model.Section, slotID string, teachers []model.Teacher) bool {
    for _, t := range teachers {
        if t.TeacherID != sec.TeacherID {
            continue
        }
        for _, s := range t.Slots {
            if s == slotID {
                return true
            }
        }
        return false
    }
    return false
}
