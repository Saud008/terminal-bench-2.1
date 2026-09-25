package walkreport

import "github.com/terminus/overbookctl/internal/model"

func normalizeAtlasPayload(assignments []model.RoomAssignment, walks []model.WalkEntry) ([]model.RoomAssignment, []model.WalkEntry) {
    return assignments, walks
}
