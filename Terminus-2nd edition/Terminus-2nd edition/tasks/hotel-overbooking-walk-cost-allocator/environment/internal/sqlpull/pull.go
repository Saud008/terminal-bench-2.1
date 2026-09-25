package sqlpull

import (
    "database/sql"
    "fmt"

    _ "modernc.org/sqlite"

    "github.com/terminus/overbookctl/internal/model"
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
    row := db.QueryRow(`SELECT scenario, night_date, catalog_seed FROM scenario_meta LIMIT 1`)
    if err := row.Scan(&meta.Scenario, &meta.NightDate, &meta.CatalogSeed); err != nil {
        return meta, fmt.Errorf("scenario_meta: %w", err)
    }
    return meta, nil
}

func ReadRoomTypes(db *sql.DB) ([]model.RoomType, error) {
    rows, err := db.Query(`SELECT room_type_id, name, rank FROM room_types ORDER BY room_type_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.RoomType
    for rows.Next() {
        var rt model.RoomType
        if err := rows.Scan(&rt.RoomTypeID, &rt.Name, &rt.Rank); err != nil {
            return nil, err
        }
        out = append(out, rt)
    }
    return out, rows.Err()
}

func ReadRooms(db *sql.DB) ([]model.Room, error) {
    rows, err := db.Query(`SELECT room_id, room_type_id, status FROM rooms ORDER BY room_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Room
    for rows.Next() {
        var r model.Room
        if err := rows.Scan(&r.RoomID, &r.RoomTypeID, &r.Status); err != nil {
            return nil, err
        }
        out = append(out, r)
    }
    return out, rows.Err()
}

func ReadMaintenance(db *sql.DB) ([]model.Maintenance, error) {
    rows, err := db.Query(`SELECT room_id, start_date, end_date FROM maintenance_windows ORDER BY room_id, start_date`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Maintenance
    for rows.Next() {
        var m model.Maintenance
        if err := rows.Scan(&m.RoomID, &m.StartDate, &m.EndDate); err != nil {
            return nil, err
        }
        out = append(out, m)
    }
    return out, rows.Err()
}

func ReadLoyalty(db *sql.DB) ([]model.LoyaltyPolicy, error) {
    rows, err := db.Query(`SELECT tier_name, protection_rank FROM loyalty_policies ORDER BY protection_rank, tier_name`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.LoyaltyPolicy
    for rows.Next() {
        var p model.LoyaltyPolicy
        if err := rows.Scan(&p.TierName, &p.ProtectionRank); err != nil {
            return nil, err
        }
        out = append(out, p)
    }
    return out, rows.Err()
}

func ReadSubstitutions(db *sql.DB) ([]model.SubstitutionRule, error) {
    rows, err := db.Query(`SELECT from_type_id, to_type_id FROM substitution_rules ORDER BY from_type_id, to_type_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.SubstitutionRule
    for rows.Next() {
        var s model.SubstitutionRule
        if err := rows.Scan(&s.FromTypeID, &s.ToTypeID); err != nil {
            return nil, err
        }
        out = append(out, s)
    }
    return out, rows.Err()
}

func ReadWalkCosts(db *sql.DB) ([]model.WalkCost, error) {
    rows, err := db.Query(`SELECT from_type_id, to_type_id, cost_cents FROM walk_costs ORDER BY from_type_id, to_type_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.WalkCost
    for rows.Next() {
        var wc model.WalkCost
        if err := rows.Scan(&wc.FromTypeID, &wc.ToTypeID, &wc.CostCents); err != nil {
            return nil, err
        }
        out = append(out, wc)
    }
    return out, rows.Err()
}
