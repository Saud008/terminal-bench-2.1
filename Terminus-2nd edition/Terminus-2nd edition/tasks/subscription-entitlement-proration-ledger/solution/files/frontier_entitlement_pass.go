package entitlementrun

import (
    "database/sql"
    "sort"
    "time"

    "github.com/terminus/subledctl/internal/anchorsync"
    "github.com/terminus/subledctl/internal/couponstack"
    "github.com/terminus/subledctl/internal/metercarry"
    "github.com/terminus/subledctl/internal/model"
    "github.com/terminus/subledctl/internal/prorateengine"
    "github.com/terminus/subledctl/internal/entsnap"
    "github.com/terminus/subledctl/internal/store"
)

type planInfo struct {
    prorateengine.Plan
    Included int
    Overage  int64
}

type changeRow struct {
    EventDate string
    FromPlan  string
    ToPlan    string
}

func RunEntitlementPass() error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    cycleStart, _ := store.GetMeta(db, "cycle_start")
    cycleEnd, _ := store.GetMeta(db, "cycle_end")
    initialPlan, _ := store.GetMeta(db, "initial_plan")
    changes, err := loadPlanChanges(db)
    if err != nil {
        return err
    }
    shifts, _ := loadShifts(db)
    plans, err := loadPlans(db)
    if err != nil {
        return err
    }
    usageByDate, err := loadUsage(db)
    if err != nil {
        return err
    }
    segments := buildSegments(initialPlan, changes, cycleStart, cycleEnd, shifts, plans)
    if _, err := entsnap.WriteEntitlementSnap(segments); err != nil {
        return err
    }
    if err := persistSegments(db, segments); err != nil {
        return err
    }
    coupons, _ := loadCoupons(db)
    carry := 0
    pass := readPass() + 1
    for i, seg := range segments {
        plan := plans[seg.PlanID]
        usage := sumUsageInRange(usageByDate, seg.WindowStart, seg.WindowEnd)
        overUnits := metercarry.OverageUnits(plan.Included, usage, carry)
        overCents := int64(overUnits) * plan.Overage
        subtotal := seg.BaseCents + overCents
        disc := couponstack.ApplyCoupons(subtotal, coupons)
        _, _ = db.Exec(`INSERT INTO ledger(line_kind,segment_index,amount_cents,pass_num) VALUES(?,?,?,?)`,
            "segment", seg.SegmentIndex, subtotal-disc, pass)
        if i < len(changes) {
            ch := changes[i]
            if plans[ch.ToPlan].MonthlyCents < plans[ch.FromPlan].MonthlyCents {
                carry = metercarry.CarryUnits(plans[ch.FromPlan].Included, usage)
            } else {
                carry = 0
            }
        }
    }
    return nil
}

func buildSegments(initial string, changes []changeRow, cycleStart, cycleEnd string, shifts []anchorsync.Shift, plans map[string]planInfo) []model.Segment {
    bounds := []string{cycleStart}
    for _, ch := range changes {
        bounds = append(bounds, ch.EventDate)
    }
    bounds = append(bounds, cycleEnd)
    planIDs := []string{initial}
    for _, ch := range changes {
        planIDs = append(planIDs, ch.ToPlan)
    }
    var out []model.Segment
    for i, pid := range planIDs {
        segStart := bounds[i]
        var segEnd string
        if i < len(planIDs)-1 {
            t, _ := time.Parse("2006-01-02", bounds[i+1])
            segEnd = t.AddDate(0, 0, -1).Format("2006-01-02")
        } else {
            segEnd = cycleEnd
        }
        segEnd = anchorsync.AdjustWindowEnd(segStart, segEnd, cycleEnd, shifts)
        plan := plans[pid]
        base, days, _ := prorateengine.SegmentBase(plan.MonthlyCents, segStart, segEnd, cycleStart, cycleEnd)
        if i > 0 {
            prev := changes[i-1]
            credit, _ := prorateengine.ChangeCredit(plans[prev.FromPlan].MonthlyCents, prev.EventDate, cycleStart, cycleEnd)
            base -= credit
        }
        out = append(out, model.Segment{
            SegmentIndex: i,
            PlanID:       pid,
            WindowStart:  segStart,
            WindowEnd:    segEnd,
            SegmentDays:  days,
            BaseCents:    base,
        })
    }
    sort.Slice(out, func(i, j int) bool { return out[i].SegmentIndex < out[j].SegmentIndex })
    return out
}

func loadPlanChanges(db *sql.DB) ([]changeRow, error) {
    rs, err := db.Query(`SELECT event_date,from_plan,to_plan FROM events WHERE event_type='plan_change' ORDER BY event_date`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []changeRow
    for rs.Next() {
        var r changeRow
        if err := rs.Scan(&r.EventDate, &r.FromPlan, &r.ToPlan); err != nil {
            return nil, err
        }
        out = append(out, r)
    }
    return out, rs.Err()
}

func loadShifts(db *sql.DB) ([]anchorsync.Shift, error) {
    rs, err := db.Query(`SELECT effective_date,new_anchor_day FROM anchor_shifts ORDER BY effective_date`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []anchorsync.Shift
    for rs.Next() {
        var s anchorsync.Shift
        if err := rs.Scan(&s.EffectiveDate, &s.NewAnchorDay); err != nil {
            return nil, err
        }
        out = append(out, s)
    }
    return out, rs.Err()
}

func loadPlans(db *sql.DB) (map[string]planInfo, error) {
    rs, err := db.Query(`SELECT plan_id,monthly_cents,included_units,overage_cents FROM plans`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    m := map[string]planInfo{}
    for rs.Next() {
        var pid string
        var monthly int64
        var inc int
        var over int64
        if err := rs.Scan(&pid, &monthly, &inc, &over); err != nil {
            return nil, err
        }
        m[pid] = planInfo{Plan: prorateengine.Plan{PlanID: pid, MonthlyCents: monthly}, Included: inc, Overage: over}
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

func loadCoupons(db *sql.DB) ([]couponstack.Coupon, error) {
    rs, err := db.Query(`SELECT coupon_id,precedence,kind,value,stackable FROM coupons ORDER BY precedence`)
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

func sumUsageInRange(m map[string]int, start, end string) int {
    total := 0
    for d, u := range m {
        if d >= start && d <= end {
            total += u
        }
    }
    return total
}

func persistSegments(db *sql.DB, segs []model.Segment) error {
    if _, err := db.Exec(`DELETE FROM segments`); err != nil {
        return err
    }
    for _, s := range segs {
        if _, err := db.Exec(`INSERT INTO segments(segment_index,plan_id,window_start,window_end,segment_days,base_cents) VALUES(?,?,?,?,?,?)`,
            s.SegmentIndex, s.PlanID, s.WindowStart, s.WindowEnd, s.SegmentDays, s.BaseCents); err != nil {
            return err
        }
    }
    return nil
}

func readPass() int {
    return 0
}
