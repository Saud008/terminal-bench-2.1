package settlementemit

import (
    "crypto/sha256"
    "database/sql"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "sort"

    "github.com/terminus/auctctl/internal/postsaleadj"
    "github.com/terminus/auctctl/internal/collateralnet"
    "github.com/terminus/auctctl/internal/model"
    "github.com/terminus/auctctl/internal/buyerfee"
    "github.com/terminus/auctctl/internal/store"
)

func PublishInvoices(scenario string, outPath string) error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    pass := readPass()
    if pass <= 0 {
        return fmt.Errorf("adjudication_pass must be positive")
    }
    sid, err := store.GetMeta(db, "scenario_id")
    if err != nil {
        return err
    }
    awards, err := loadAwards(db)
    if err != nil {
        return err
    }
    tiers, err := loadTiers(db)
    if err != nil {
        return err
    }
    invoices := make([]model.InvoiceLine, 0)
    for _, aw := range awards {
        if aw.Status != "awarded" {
            continue
        }
        tier := tiers[aw.LotID]
        prem, err := buyerfee.BuyerPremiumCents(aw.HammerCents, tier)
        if err != nil {
            return err
        }
        adjCents, err := postsaleadj.LotAdjustmentCents(db, aw.LotID, aw.BidderID)
        if err != nil {
            return err
        }
        subtotal := aw.HammerCents + prem + adjCents
        rem, err := collateralnet.RemainingDeposit(db, aw.BidderID)
        if err != nil {
            return err
        }
        applied := rem
        if applied > subtotal {
            applied = subtotal
        }
        due := subtotal - applied
        if err := collateralnet.ApplyDeposit(db, aw.BidderID, applied); err != nil {
            return err
        }
        invoices = append(invoices, model.InvoiceLine{
            LotID:           aw.LotID,
            BidderID:        aw.BidderID,
            HammerCents:     aw.HammerCents,
            PremiumCents:    prem,
            AdjustmentCents: adjCents,
            DepositApplied:  applied,
            AmountDueCents:  due,
        })
        _, _ = db.Exec(`INSERT INTO ledger(lot_id,bidder_id,line_kind,amount_cents,pass_num) VALUES(?,?,?,?,?)`,
            aw.LotID, aw.BidderID, "invoice", due, pass)
    }
    sort.Slice(invoices, func(i, j int) bool {
        if invoices[i].LotID == invoices[j].LotID {
            return invoices[i].BidderID < invoices[j].BidderID
        }
        return invoices[i].LotID < invoices[j].LotID
    })
    digest := digestInvoices(invoices)
    rep := model.InvoiceReport{
        ScenarioID:       sid,
        AdjudicationPass: pass,
        Invoices:         invoices,
        LedgerDigest:     digest,
    }
    raw, err := json.MarshalIndent(rep, "", "  ")
    if err != nil {
        return err
    }
    raw = append(raw, '\n')
    if outPath == "" {
        outPath = "/app/output/buyer-invoices.json"
    }
    return os.WriteFile(outPath, raw, 0o644)
}

type awardRow struct {
    LotID       string
    Status      string
    BidderID    string
    HammerCents int64
}

func loadAwards(db *sql.DB) ([]awardRow, error) {
    rs, err := db.Query(`SELECT lot_id,status,bidder_id,hammer_cents FROM awards ORDER BY lot_id`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []awardRow
    for rs.Next() {
        var a awardRow
        if err := rs.Scan(&a.LotID, &a.Status, &a.BidderID, &a.HammerCents); err != nil {
            return nil, err
        }
        out = append(out, a)
    }
    return out, rs.Err()
}

func loadTiers(db *sql.DB) (map[string]string, error) {
    rs, err := db.Query(`SELECT lot_id, premium_tier FROM lots`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    m := map[string]string{}
    for rs.Next() {
        var lot, tier string
        if err := rs.Scan(&lot, &tier); err != nil {
            return nil, err
        }
        m[lot] = tier
    }
    return m, rs.Err()
}

func readPass() int {
    raw, err := os.ReadFile("/app/state/adjudication-pass.json")
    if err != nil {
        return 0
    }
    var body struct {
        AdjudicationPass int `json:"adjudication_pass"`
    }
    if json.Unmarshal(raw, &body) != nil {
        return 0
    }
    return body.AdjudicationPass
}

func digestInvoices(lines []model.InvoiceLine) string {
    raw, _ := json.Marshal(lines)
    sum := sha256.Sum256(raw)
    return hex.EncodeToString(sum[:])
}
