package a11yshield

import "github.com/terminus/venuetixctl/internal/model"

func AllowsAccessible(seat model.Seat, section model.Section, assigned map[string]bool, seats []model.Seat) bool {
    if !seat.Accessible {
        return true
    }
    remaining := 0
    for _, s := range seats {
        if s.SectionID != seat.SectionID || !s.Accessible {
            continue
        }
        if !assigned[s.SeatID] && s.SeatID != seat.SeatID {
            remaining++
        }
    }
    return remaining >= section.AccessibilityMin
}
