package collateralnet

import (
    "database/sql"

    "github.com/terminus/auctctl/internal/store"
)

func RemainingDeposit(db *sql.DB, bidderID string) (int64, error) {
    var total int64
    err := db.QueryRow(`SELECT deposit_cents FROM deposits WHERE bidder_id=?`, bidderID).Scan(&total)
    if err == sql.ErrNoRows {
        return 0, nil
    }
    if err != nil {
        return 0, err
    }
    var applied int64
    _ = db.QueryRow(`SELECT applied_cents FROM deposit_applied WHERE bidder_id=?`, bidderID).Scan(&applied)
    return total - applied, nil
}

func ApplyDeposit(db *sql.DB, bidderID string, amount int64) error {
    var applied int64
    err := db.QueryRow(`SELECT applied_cents FROM deposit_applied WHERE bidder_id=?`, bidderID).Scan(&applied)
    if err == sql.ErrNoRows {
        _, err = db.Exec(`INSERT INTO deposit_applied(bidder_id,applied_cents) VALUES(?,?)`, bidderID, amount)
        return err
    }
    if err != nil {
        return err
    }
    _, err = db.Exec(`UPDATE deposit_applied SET applied_cents=applied_cents+? WHERE bidder_id=?`, amount, bidderID)
    return err
}

func OpenDB() (*sql.DB, error) {
    return store.Open()
}
