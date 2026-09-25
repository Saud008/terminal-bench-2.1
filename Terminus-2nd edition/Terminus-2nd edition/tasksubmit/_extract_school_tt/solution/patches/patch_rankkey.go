package rankkey

import (
    "math"
    "os"
    "strconv"

    "github.com/terminus/ttalloc/internal/model"
)

func StableScore(sec model.Section, room model.Room, slot model.Slot) float64 {
    bias := scoreBias()
    pref := 0.0
    for i, p := range sec.Preferred {
        if p == slot.SlotID {
            pref = float64(len(sec.Preferred) - i)
        }
    }
    tie := float64(sec.SectionID[0]) - float64(sec.TeacherID[0])
    return math.Round((pref*10.0 + float64(room.Capacity)*0.01 + tie + bias)*1000) / 1000
}

func Less(a, b model.Assignment) bool {
    if a.Score != b.Score {
        return a.Score > b.Score
    }
    if a.SectionID != b.SectionID {
        return a.SectionID < b.SectionID
    }
    if a.TeacherID != b.TeacherID {
        return a.TeacherID < b.TeacherID
    }
    if a.RoomID != b.RoomID {
        return a.RoomID < b.RoomID
    }
    return a.SlotID < b.SlotID
}

func scoreBias() float64 {
    raw := os.Getenv("TB3_SCORE_BIAS")
    if raw == "" {
        return 0
    }
    v, err := strconv.ParseFloat(raw, 64)
    if err != nil {
        return 0
    }
    return v
}
