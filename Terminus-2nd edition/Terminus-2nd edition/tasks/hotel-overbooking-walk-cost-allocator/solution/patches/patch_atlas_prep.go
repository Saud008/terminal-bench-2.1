package walkreport

import "github.com/terminus/overbookctl/internal/model"

func normalizeAtlasPayload(assignments []model.RoomAssignment, walks []model.WalkEntry) ([]model.RoomAssignment, []model.WalkEntry) {
    if assignments == nil {
        assignments = []model.RoomAssignment{}
    }
    if walks == nil {
        walks = []model.WalkEntry{}
    }
    return assignments, walks
}
