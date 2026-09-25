package invoicepub

import (
    "crypto/sha256"
    "database/sql"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "sort"

    "github.com/terminus/subledctl/internal/couponstack"
    "github.com/terminus/subledctl/internal/metercarry"
    "github.com/terminus/subledctl/internal/model"
    "github.com/terminus/subledctl/internal/store"
)

func PublishInvoices(scenario, outPath string) error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    pass := readPass()
    if pass <= 0 {
        return fmt.Errorf("reconcile_pass must be positive")
    }
    sid, err := store.GetMeta(db, "scenario_id")
    if err != nil {
        return err
    }
    cust, _ := store.GetMeta(db, "customer_id")
    segs, err := loadSegments(db)
    if err != nil {
        return err
    }
    plans, err := loadPlans(db)
    if err != nil {
        return err
    }
    usage, err := loadUsage(db)
    if err != nil {
        return err
    }
    coupons, _ := loadCoupons(db)
    changes, _ := loadChanges(db)
    carry := 0
    lines := make([]model.InvoiceLine, 0)
    for i, s := range segs {
        plan := plans[s.PlanID]
        u := sumUsage(usage, s.WindowStart, s.WindowEnd)
        overUnits := metercarry.OverageUnits(plan.Included, u, carry)
        overCents := int64(overUnits) * plan.Overage
        subtotal := s.BaseCents + overCents
        disc := couponstack.ApplyCoupons(subtotal, coupons)
        lines = append(lines, model.InvoiceLine{
            SegmentIndex:   s.SegmentIndex,
            LineKind:       "subscription",
            PlanID:         s.PlanID,
            BaseCents:      s.BaseCents,
            ProrationCents: 0,
            OverageCents:   overCents,
            CouponCents:    disc,
            TotalCents:     subtotal - disc,
        })
        if i < len(changes) {
            ch := changes[i]
            if plans[ch.ToPlan].MonthlyCents < plans[ch.FromPlan].MonthlyCents {
                carry = metercarry.CarryUnits(plans[ch.FromPlan].Included, u)
            } else {
                carry = 0
            }
        }
    }
    sort.Slice(lines, func(i, j int) bool {
        if lines[i].LineKind == lines[j].LineKind {
            return lines[i].SegmentIndex < lines[j].SegmentIndex
        }
        return lines[i].LineKind < lines[j].LineKind
    })
    digest := digestLines(lines)
    rep := model.InvoiceReport{
        ScenarioID:    sid,
        CustomerID:    cust,
        ReconcilePass: pass,
        InvoiceLines:  lines,
        LedgerDigest:  digest,
    }
    raw, err := json.MarshalIndent(rep, "", "  ")
    if err != nil {
        return err
    }
    raw = append(raw, '\n')
    if outPath == "" {
        outPath = "/app/output/subscription-invoices.json"
    }
    if err := os.WriteFile(outPath, raw, 0o644); err != nil {
        return err
    }
    jl, _ := json.Marshal(lines)
    return os.WriteFile("/app/output/entitlement-ledger.jsonl", append(jl, '\n'), 0o644)
}

type segRow struct {
    SegmentIndex int
    PlanID       string
    WindowStart  string
    WindowEnd    string
    BaseCents    int64
}

type planRow struct {
    MonthlyCents int64
    Included     int
    Overage      int64
}

type changeRow struct {
    FromPlan string
    ToPlan   string
}

func loadSegments(db *sql.DB) ([]segRow, error) {
    rs, err := db.Query(`SELECT segment_index,plan_id,window_start,window_end,base_cents FROM segments ORDER BY segment_index`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []segRow
    for rs.Next() {
        var s segRow
        if err := rs.Scan(&s.SegmentIndex, &s.PlanID, &s.WindowStart, &s.WindowEnd, &s.BaseCents); err != nil {
            return nil, err
        }
        out = append(out, s)
    }
    return out, rs.Err()
}

func loadPlans(db *sql.DB) (map[string]planRow, error) {
    rs, err := db.Query(`SELECT plan_id,monthly_cents,included_units,overage_cents FROM plans`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    m := map[string]planRow{}
    for rs.Next() {
        var pid string
        var p planRow
        if err := rs.Scan(&pid, &p.MonthlyCents, &p.Included, &p.Overage); err != nil {
            return nil, err
        }
        m[pid] = p
    }
    return m, rs.Err()
}

func loadUsage(db *sql.DB) (map[string]int, error) {
    rs, err := db.Query(`SELECT event_date, units FROM events WHERE event_type='usage'`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    m := map[string]int{}
    for rs.Next() {
        var d string
        var u int
        if err := rs.Scan(&d, &u); err != nil {
            return nil, err
        }
        m[d] += u
    }
    return m, rs.Err()
}

func loadChanges(db *sql.DB) ([]changeRow, error) {
    rs, err := db.Query(`SELECT from_plan,to_plan FROM events WHERE event_type='plan_change' ORDER BY event_date`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []changeRow
    for rs.Next() {
        var r changeRow
        if err := rs.Scan(&r.FromPlan, &r.ToPlan); err != nil {
            return nil, err
        }
        out = append(out, r)
    }
    return out, rs.Err()
}

func loadCoupons(db *sql.DB) ([]couponstack.Coupon, error) {
    rs, err := db.Query(`SELECT coupon_id,precedence,kind,value,stackable FROM coupons`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []couponstack.Coupon
    for rs.Next() {
        var c couponstack.Coupon
        var stack int
        if err := rs.Scan(&c.CouponID, &c.Precedence, &c.Kind, &c.Value, &stack); err != nil {
            return nil, err
        }
        c.Stackable = stack == 1
        out = append(out, c)
    }
    return out, rs.Err()
}

func sumUsage(m map[string]int, start, end string) int {
    t := 0
    for d, u := range m {
        if d >= start && d <= end {
            t += u
        }
    }
    return t
}

func readPass() int {
    raw, err := os.ReadFile("/app/state/reconcile-pass.json")
    if err != nil {
        return 0
    }
    var body struct {
        ReconcilePass int `json:"reconcile_pass"`
    }
    if json.Unmarshal(raw, &body) != nil {
        return 0
    }
    return body.ReconcilePass
}

func digestLines(lines []model.InvoiceLine) string {
    raw, _ := json.Marshal(lines)
    sum := sha256.Sum256(raw)
    return hex.EncodeToString(sum[:])
}
