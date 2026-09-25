package scenarioload

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"

    "github.com/terminus/auctctl/internal/model"
    "github.com/terminus/auctctl/internal/store"
)

func LoadScenario(scenario, fixtureDir string) (*model.Scenario, error) {
    path := filepath.Join(fixtureDir, "scenarios", scenario+".json")
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var sc model.Scenario
    if err := json.Unmarshal(raw, &sc); err != nil {
        return nil, err
    }
    return &sc, nil
}

func PersistCatalog(sc *model.Scenario) error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    if _, err := db.Exec(`DELETE FROM lots`); err != nil {
        return err
    }
    if _, err := db.Exec(`DELETE FROM bids`); err != nil {
        return err
    }
    if _, err := db.Exec(`DELETE FROM deposits`); err != nil {
        return err
    }
    if _, err := db.Exec(`DELETE FROM adjustments`); err != nil {
        return err
    }
    if _, err := db.Exec(`DELETE FROM awards`); err != nil {
        return err
    }
    if err := store.SetMeta(db, "scenario_id", sc.ScenarioID); err != nil {
        return err
    }
    premiumRaw, _ := json.Marshal(sc.PremiumSchedule)
    if err := store.SetMeta(db, "premium_schedule", string(premiumRaw)); err != nil {
        return err
    }
    for _, lot := range sc.Lots {
        w := 0
        if lot.Withdrawn {
            w = 1
        }
        if _, err := db.Exec(`INSERT INTO lots(lot_id,reserve_cents,withdrawn,premium_tier) VALUES(?,?,?,?)`,
            lot.LotID, lot.ReserveCents, w, lot.PremiumTier); err != nil {
            return err
        }
    }
    for _, bid := range sc.Bids {
        if _, err := db.Exec(`INSERT INTO bids(lot_id,bidder_id,amount_cents,bid_seq,bid_ts) VALUES(?,?,?,?,?)`,
            bid.LotID, bid.BidderID, bid.AmountCents, bid.BidSeq, bid.BidTS); err != nil {
            return err
        }
    }
    for _, dep := range sc.Deposits {
        if _, err := db.Exec(`INSERT INTO deposits(bidder_id,deposit_cents) VALUES(?,?)`, dep.BidderID, dep.DepositCents); err != nil {
            return err
        }
    }
    for _, adj := range sc.Adjustments {
        if _, err := db.Exec(`INSERT INTO adjustments(lot_id,bidder_id,adjustment_cents) VALUES(?,?,?)`,
            adj.LotID, adj.BidderID, adj.AdjustmentCents); err != nil {
            return err
        }
    }
    return nil
}

func CatalogLoaded(scenario string) error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    sid, err := store.GetMeta(db, "scenario_id")
    if err != nil || sid != scenario {
        return fmt.Errorf("catalog not loaded for %s", scenario)
    }
    return nil
}
