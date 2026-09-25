package adjacency

import (
    "sort"

    "github.com/terminus/venuetixctl/internal/model"
)

func AllowsAssignment(seat model.Seat, assigned map[string]bool, seats []model.Seat) bool {
    rowSeats := seatsInRow(seats, seat.SectionID, seat.RowNum)
    if len(rowSeats) == 0 {
        return true
    }
    trial := map[string]bool{}
    for k, v := range assigned {
        trial[k] = v
    }
    trial[seat.SeatID] = true
    return !createsOrphan(rowSeats, trial)
}

func seatsInRow(seats []model.Seat, sectionID string, rowNum int) []model.Seat {
    var out []model.Seat
    for _, s := range seats {
        if s.SectionID == sectionID && s.RowNum == rowNum {
            out = append(out, s)
        }
    }
    sort.Slice(out, func(i, j int) bool { return out[i].SeatNum < out[j].SeatNum })
    return out
}

func createsOrphan(rowSeats []model.Seat, assigned map[string]bool) bool {
    for i := 1; i < len(rowSeats)-1; i++ {
        left := assigned[rowSeats[i-1].SeatID]
        mid := !assigned[rowSeats[i].SeatID]
        right := assigned[rowSeats[i+1].SeatID]
        if left && mid && right {
            return true
        }
    }
    return false
}
