package dbread

import (
    "database/sql"
    "fmt"

    _ "modernc.org/sqlite"

    "github.com/terminus/holdfairctl/internal/model"
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
    row := db.QueryRow(`SELECT scenario, reconcile_date, catalog_seed FROM scenario_meta LIMIT 1`)
    if err := row.Scan(&meta.Scenario, &meta.ReconcileDate, &meta.CatalogSeed); err != nil {
        return meta, fmt.Errorf("scenario_meta: %w", err)
    }
    return meta, nil
}

func ReadBranches(db *sql.DB) ([]model.Branch, error) {
    rows, err := db.Query(`SELECT branch_id, name, allows_interbranch_transfer FROM branches ORDER BY branch_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Branch
    for rows.Next() {
        var b model.Branch
        var allow int
        if err := rows.Scan(&b.BranchID, &b.Name, &allow); err != nil {
            return nil, err
        }
        b.AllowsInterbranchTransfer = allow != 0
        out = append(out, b)
    }
    return out, rows.Err()
}

func ReadPatrons(db *sql.DB) ([]model.Patron, error) {
    rows, err := db.Query(`SELECT patron_id, home_branch_id, priority_class FROM patrons ORDER BY patron_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Patron
    for rows.Next() {
        var p model.Patron
        if err := rows.Scan(&p.PatronID, &p.HomeBranchID, &p.PriorityClass); err != nil {
            return nil, err
        }
        out = append(out, p)
    }
    return out, rows.Err()
}

func ReadHolds(db *sql.DB) ([]model.HoldRequest, error) {
    rows, err := db.Query(`SELECT request_id, patron_id, item_id, pickup_branch_id, hold_date FROM hold_requests ORDER BY request_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.HoldRequest
    for rows.Next() {
        var h model.HoldRequest
        if err := rows.Scan(&h.RequestID, &h.PatronID, &h.ItemID, &h.PickupBranchID, &h.HoldDate); err != nil {
            return nil, err
        }
        out = append(out, h)
    }
    return out, rows.Err()
}

func ReadCopies(db *sql.DB) ([]model.ItemCopy, error) {
    rows, err := db.Query(`SELECT copy_id, item_id, branch_id, status FROM item_copies ORDER BY copy_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.ItemCopy
    for rows.Next() {
        var c model.ItemCopy
        if err := rows.Scan(&c.CopyID, &c.ItemID, &c.BranchID, &c.Status); err != nil {
            return nil, err
        }
        out = append(out, c)
    }
    return out, rows.Err()
}

func ReadSuspensions(db *sql.DB) ([]model.Suspension, error) {
    rows, err := db.Query(`SELECT patron_id, start_date, end_date FROM suspension_windows ORDER BY patron_id, start_date`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Suspension
    for rows.Next() {
        var s model.Suspension
        if err := rows.Scan(&s.PatronID, &s.StartDate, &s.EndDate); err != nil {
            return nil, err
        }
        out = append(out, s)
    }
    return out, rows.Err()
}

func ReadPolicies(db *sql.DB) ([]model.PriorityPolicy, error) {
    rows, err := db.Query(`SELECT class_name, rank FROM priority_policies ORDER BY rank, class_name`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.PriorityPolicy
    for rows.Next() {
        var p model.PriorityPolicy
        if err := rows.Scan(&p.ClassName, &p.Rank); err != nil {
            return nil, err
        }
        out = append(out, p)
    }
    return out, rows.Err()
}
