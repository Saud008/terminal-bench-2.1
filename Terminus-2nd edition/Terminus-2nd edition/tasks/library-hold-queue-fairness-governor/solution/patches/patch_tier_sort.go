package priqueue

import (
    "sort"

    "github.com/terminus/holdfairctl/internal/model"
)

type RankedHold struct {
    Hold     model.HoldRequest
    TierRank int
}

func SortHolds(holds []RankedHold) {
    sort.SliceStable(holds, func(i, j int) bool {
        if holds[i].TierRank != holds[j].TierRank {
            return holds[i].TierRank < holds[j].TierRank
        }
        if holds[i].Hold.HoldDate != holds[j].Hold.HoldDate {
            return holds[i].Hold.HoldDate < holds[j].Hold.HoldDate
        }
        return holds[i].Hold.PatronID < holds[j].Hold.PatronID
    })
}
