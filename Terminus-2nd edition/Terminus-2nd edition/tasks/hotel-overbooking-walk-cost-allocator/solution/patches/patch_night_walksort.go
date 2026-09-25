package nightopt

import (
    "github.com/terminus/overbookctl/internal/model"
    "sort"
)

func sortPlanWalks(walks []model.WalkEntry) {
    sort.Slice(walks, func(i, j int) bool {
        if walks[i].WalkCostCents != walks[j].WalkCostCents {
            return walks[i].WalkCostCents < walks[j].WalkCostCents
        }
        return walks[i].ReservationID < walks[j].ReservationID
    })
}
