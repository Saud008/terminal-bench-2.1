package lotverdict

import (
    "database/sql"
    "sort"

    "github.com/terminus/auctctl/internal/model"
    "github.com/terminus/auctctl/internal/store"
)

type bidRow struct {
    LotID       string
    BidderID    string
    AmountCents int64
    BidSeq      int
    BidTS       string
}

func RunAdjudication() error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    if _, err := db.Exec(`DELETE FROM awards`); err != nil {
        return err
    }
    lots, err := fetchLots(db)
    if err != nil {
        return err
    }
    bids, err := fetchBids(db)
    if err != nil {
        return err
    }
    byLot := map[string][]bidRow{}
    for _, b := range bids {
        byLot[b.LotID] = append(byLot[b.LotID], b)
    }
    for _, lot := range lots {
        aw := model.Award{LotID: lot.LotID, Status: "passed"}
        rows := byLot[lot.LotID]
        if len(rows) == 0 {
            if err := insertAward(db, aw); err != nil {
                return err
            }
            continue
        }
        sort.Slice(rows, func(i, j int) bool {
            return rows[i].AmountCents > rows[j].AmountCents
        })
        top := rows[0]
        if top.AmountCents > lot.ReserveCents {
            aw.Status = "awarded"
            aw.BidderID = top.BidderID
            aw.HammerCents = top.AmountCents
        }
        if err := insertAward(db, aw); err != nil {
            return err
        }
    }
    return nil
}

type lotRow struct {
    LotID        string
    ReserveCents int64
    Withdrawn    bool
    PremiumTier  string
}

func fetchLots(db *sql.DB) ([]lotRow, error) {
    rs, err := db.Query(`SELECT lot_id, reserve_cents, withdrawn, premium_tier FROM lots ORDER BY lot_id`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []lotRow
    for rs.Next() {
        var l lotRow
        var w int
        if err := rs.Scan(&l.LotID, &l.ReserveCents, &w, &l.PremiumTier); err != nil {
            return nil, err
        }
        l.Withdrawn = w == 1
        out = append(out, l)
    }
    return out, rs.Err()
}

func fetchBids(db *sql.DB) ([]bidRow, error) {
    rs, err := db.Query(`SELECT lot_id, bidder_id, amount_cents, bid_seq, bid_ts FROM bids`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []bidRow
    for rs.Next() {
        var b bidRow
        if err := rs.Scan(&b.LotID, &b.BidderID, &b.AmountCents, &b.BidSeq, &b.BidTS); err != nil {
            return nil, err
        }
        out = append(out, b)
    }
    return out, rs.Err()
}

func insertAward(db *sql.DB, aw model.Award) error {
    _, err := db.Exec(`INSERT INTO awards(lot_id,status,bidder_id,hammer_cents) VALUES(?,?,?,?)`,
        aw.LotID, aw.Status, aw.BidderID, aw.HammerCents)
    return err
}
