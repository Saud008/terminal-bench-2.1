package cycleload

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"

    "github.com/terminus/subledctl/internal/store"
)

type Scenario struct {
    ScenarioID      string            `json:"scenario_id"`
    CustomerID      string            `json:"customer_id"`
    CycleStart      string            `json:"cycle_start"`
    CycleEnd        string            `json:"cycle_end"`
    BillingAnchorDay int              `json:"billing_anchor_day"`
    InitialPlan     string            `json:"initial_plan"`
    Plans           map[string]Plan   `json:"plans"`
    Events          []Event           `json:"events"`
    Coupons         []Coupon          `json:"coupons"`
    AnchorShifts    []AnchorShift     `json:"anchor_shifts"`
}

type Plan struct {
    MonthlyCents  int64 `json:"monthly_cents"`
    IncludedUnits int   `json:"included_units"`
    OverageCents  int64 `json:"overage_cents"`
}

type Event struct {
    EventType string `json:"event_type"`
    EventDate string `json:"event_date"`
    FromPlan  string `json:"from_plan"`
    ToPlan    string `json:"to_plan"`
    Units     int    `json:"units"`
}

type Coupon struct {
    CouponID   string `json:"coupon_id"`
    Precedence int    `json:"precedence"`
    Kind       string `json:"kind"`
    Value      int64  `json:"value"`
    Stackable  bool   `json:"stackable"`
}

type AnchorShift struct {
    EffectiveDate string `json:"effective_date"`
    NewAnchorDay  int    `json:"new_anchor_day"`
}

func LoadScenario(name, fixtureDir string) (*Scenario, error) {
    path := filepath.Join(fixtureDir, "cycles", name+".json")
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var sc Scenario
    if err := json.Unmarshal(raw, &sc); err != nil {
        return nil, err
    }
    return &sc, nil
}

func PersistCycle(sc *Scenario) error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    if err := wipe(db); err != nil {
        return err
    }
    if err := store.SetMeta(db, "scenario_id", sc.ScenarioID); err != nil {
        return err
    }
    if err := store.SetMeta(db, "customer_id", sc.CustomerID); err != nil {
        return err
    }
    if err := store.SetMeta(db, "cycle_start", sc.CycleStart); err != nil {
        return err
    }
    if err := store.SetMeta(db, "cycle_end", sc.CycleEnd); err != nil {
        return err
    }
    if err := store.SetMeta(db, "initial_plan", sc.InitialPlan); err != nil {
        return err
    }
    for pid, p := range sc.Plans {
        if _, err := db.Exec(`INSERT INTO plans(plan_id,monthly_cents,included_units,overage_cents) VALUES(?,?,?,?)`,
            pid, p.MonthlyCents, p.IncludedUnits, p.OverageCents); err != nil {
            return err
        }
    }
    for _, ev := range sc.Events {
        if _, err := db.Exec(`INSERT INTO events(event_type,event_date,from_plan,to_plan,units) VALUES(?,?,?,?,?)`,
            ev.EventType, ev.EventDate, ev.FromPlan, ev.ToPlan, ev.Units); err != nil {
            return err
        }
    }
    for _, c := range sc.Coupons {
        stack := 0
        if c.Stackable {
            stack = 1
        }
        if _, err := db.Exec(`INSERT INTO coupons(coupon_id,precedence,kind,value,stackable) VALUES(?,?,?,?,?)`,
            c.CouponID, c.Precedence, c.Kind, c.Value, stack); err != nil {
            return err
        }
    }
    for _, sh := range sc.AnchorShifts {
        if _, err := db.Exec(`INSERT INTO anchor_shifts(effective_date,new_anchor_day) VALUES(?,?)`,
            sh.EffectiveDate, sh.NewAnchorDay); err != nil {
            return err
        }
    }
    return nil
}

func CycleLoaded(scenario string) error {
    db, err := store.Open()
    if err != nil {
        return err
    }
    defer db.Close()
    sid, err := store.GetMeta(db, "scenario_id")
    if err != nil {
        return fmt.Errorf("cycle not loaded")
    }
    if sid != scenario {
        return fmt.Errorf("scenario mismatch")
    }
    return nil
}

func wipe(db *sql.DB) error {
    tables := []string{"meta", "plans", "events", "coupons", "anchor_shifts", "segments", "ledger"}
    for _, t := range tables {
        if _, err := db.Exec("DELETE FROM " + t); err != nil {
            return err
        }
    }
    return nil
}
