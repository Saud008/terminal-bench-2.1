package dbread

import (
    "database/sql"
    "fmt"

    _ "modernc.org/sqlite"

    "github.com/terminus/venuetixctl/internal/model"
)

func Open(path string) (*sql.DB, error) {
    db, err := sql.Open("sqlite", path)
    if err != nil {
        return nil, err
    }
    return db, db.Ping()
}

func ReadMeta(db *sql.DB) (model.ScenarioMeta, error) {
    var meta model.ScenarioMeta
    row := db.QueryRow(`SELECT scenario, event_clock, catalog_seed FROM scenario_meta LIMIT 1`)
    if err := row.Scan(&meta.Scenario, &meta.EventClock, &meta.CatalogSeed); err != nil {
        return meta, fmt.Errorf("scenario_meta: %w", err)
    }
    return meta, nil
}

func ReadSections(db *sql.DB) ([]model.Section, error) {
    rows, err := db.Query(`SELECT section_id, name, row_count, accessibility_min FROM sections ORDER BY section_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Section
    for rows.Next() {
        var s model.Section
        if err := rows.Scan(&s.SectionID, &s.Name, &s.RowCount, &s.AccessibilityMin); err != nil {
            return nil, err
        }
        out = append(out, s)
    }
    return out, rows.Err()
}

func ReadSeats(db *sql.DB) ([]model.Seat, error) {
    rows, err := db.Query(`SELECT seat_id, section_id, row_num, seat_num, accessible FROM seats ORDER BY seat_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Seat
    for rows.Next() {
        var s model.Seat
        var acc int
        if err := rows.Scan(&s.SeatID, &s.SectionID, &s.RowNum, &s.SeatNum, &acc); err != nil {
            return nil, err
        }
        s.Accessible = acc != 0
        out = append(out, s)
    }
    return out, rows.Err()
}

func ReadOrders(db *sql.DB) ([]model.Order, error) {
    rows, err := db.Query(`SELECT order_id, patron_id, payment_rank, captured_at FROM orders ORDER BY order_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Order
    for rows.Next() {
        var o model.Order
        if err := rows.Scan(&o.OrderID, &o.PatronID, &o.PaymentRank, &o.CapturedAt); err != nil {
            return nil, err
        }
        out = append(out, o)
    }
    return out, rows.Err()
}

func ReadHolds(db *sql.DB) ([]model.SeatHold, error) {
    rows, err := db.Query(`SELECT hold_id, order_id, seat_id, expires_at, status FROM seat_holds ORDER BY hold_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.SeatHold
    for rows.Next() {
        var h model.SeatHold
        if err := rows.Scan(&h.HoldID, &h.OrderID, &h.SeatID, &h.ExpiresAt, &h.Status); err != nil {
            return nil, err
        }
        out = append(out, h)
    }
    return out, rows.Err()
}
