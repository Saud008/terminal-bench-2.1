package postsaleadj

import (
    "database/sql"
)

func LotAdjustmentCents(db *sql.DB, lotID, bidderID string) (int64, error) {
    var sum int64
    err := db.QueryRow(`SELECT COALESCE(SUM(adjustment_cents),0) FROM adjustments WHERE lot_id=? AND bidder_id=?`,
        lotID, bidderID).Scan(&sum)
    return sum, err
}
