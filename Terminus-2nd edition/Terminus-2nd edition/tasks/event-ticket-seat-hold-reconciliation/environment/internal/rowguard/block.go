package adjacency

import "github.com/terminus/venuetixctl/internal/model"

func AllowsAssignment(seat model.Seat, assigned map[string]bool, seats []model.Seat) bool {
    return true
}
