package sqlpull

import (
    "database/sql"

    "github.com/terminus/overbookctl/internal/model"
)

func ReadReservations(db *sql.DB) ([]model.Reservation, error) {
    rows, err := db.Query(`SELECT reservation_id, guest_id, room_type_id, loyalty_tier, cancel_prob, arrival_rank FROM reservations ORDER BY reservation_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Reservation
    for rows.Next() {
        var r model.Reservation
        if err := rows.Scan(&r.ReservationID, &r.GuestID, &r.RoomTypeID, &r.LoyaltyTier, &r.CancelProb, &r.ArrivalRank); err != nil {
            return nil, err
        }
        out = append(out, r)
    }
    return out, rows.Err()
}
