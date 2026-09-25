package payrank

import (
    "sort"

    "github.com/terminus/venuetixctl/internal/model"
)

type RankedHold struct {
    Hold  model.SeatHold
    Order model.Order
}

func SortHolds(holds []RankedHold) {
    sort.SliceStable(holds, func(i, j int) bool {
        if holds[i].Order.PaymentRank != holds[j].Order.PaymentRank {
            return holds[i].Order.PaymentRank > holds[j].Order.PaymentRank
        }
        if holds[i].Order.CapturedAt != holds[j].Order.CapturedAt {
            return holds[i].Order.CapturedAt > holds[j].Order.CapturedAt
        }
        return holds[i].Order.OrderID < holds[j].Order.OrderID
    })
}
