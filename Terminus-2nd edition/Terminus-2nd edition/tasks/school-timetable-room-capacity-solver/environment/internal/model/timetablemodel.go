package model

type Section struct {
    SectionID  string   `json:"section_id"`
    CourseID   string   `json:"course_id"`
    TeacherID  string   `json:"teacher_id"`
    Enrolled   int      `json:"enrolled"`
    RequiresLab bool    `json:"requires_lab"`
    SplitGroup string   `json:"split_group"`
    Preferred  []string `json:"preferred_slots"`
}

type Teacher struct {
    TeacherID string   `json:"teacher_id"`
    Slots     []string `json:"available_slots"`
}

type Room struct {
    RoomID   string `json:"room_id"`
    Capacity int    `json:"capacity"`
    RoomKind string `json:"room_kind"`
}

type Slot struct {
    SlotID string `json:"slot_id"`
    Day    string `json:"day"`
    Period int    `json:"period"`
}

type Policies struct {
    CapacityMargin int `json:"capacity_margin"`
}

type RosterBundle struct {
    Scenario string     `json:"scenario"`
    Seed     string     `json:"seed"`
    Sections []Section  `json:"sections"`
    Teachers []Teacher  `json:"teachers"`
    Rooms    []Room     `json:"rooms"`
    Slots    []Slot     `json:"slots"`
    Policies Policies   `json:"policies"`
}

type Assignment struct {
    SectionID string  `json:"section_id"`
    TeacherID string  `json:"teacher_id"`
    RoomID    string  `json:"room_id"`
    SlotID    string  `json:"slot_id"`
    Score     float64 `json:"score"`
}
