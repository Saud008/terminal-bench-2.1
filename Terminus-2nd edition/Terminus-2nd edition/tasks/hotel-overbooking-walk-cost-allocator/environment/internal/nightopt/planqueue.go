package nightopt

import (
    "github.com/terminus/overbookctl/internal/model"
    "sort"
)

type ranked struct {
    Res   model.Reservation
    Score float64
}

func sortDemandQueue(queue []ranked) {
    sort.SliceStable(queue, func(i, j int) bool {
        if queue[i].Score != queue[j].Score {
            return queue[i].Score < queue[j].Score
        }
        if queue[i].Res.ArrivalRank != queue[j].Res.ArrivalRank {
            return queue[i].Res.ArrivalRank > queue[j].Res.ArrivalRank
        }
        return queue[i].Res.ReservationID > queue[j].Res.ReservationID
    })
}
