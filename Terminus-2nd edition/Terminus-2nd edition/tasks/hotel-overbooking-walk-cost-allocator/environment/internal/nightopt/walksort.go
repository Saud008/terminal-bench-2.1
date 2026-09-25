package nightopt

import (
    "github.com/terminus/overbookctl/internal/model"
    "sort"
)

func sortPlanWalks(walks []model.WalkEntry) {
    sort.Slice(walks, func(i, j int) bool {
        return walks[i].ReservationID < walks[j].ReservationID
    })
}
