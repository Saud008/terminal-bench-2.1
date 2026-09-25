package a11yshield

import "github.com/terminus/venuetixctl/internal/model"

func AllowsAccessible(seat model.Seat, section model.Section, assigned map[string]bool, seats []model.Seat) bool {
    return true
}
