package model

type InvoiceLine struct {
    SegmentIndex   int    `json:"segment_index"`
    LineKind       string `json:"line_kind"`
    PlanID         string `json:"plan_id"`
    BaseCents      int64  `json:"base_cents"`
    ProrationCents int64  `json:"proration_cents"`
    OverageCents   int64  `json:"overage_cents"`
    CouponCents    int64  `json:"coupon_cents"`
    TotalCents     int64  `json:"total_cents"`
}

type InvoiceReport struct {
    ScenarioID     string        `json:"scenario_id"`
    CustomerID     string        `json:"customer_id"`
    ReconcilePass  int           `json:"reconcile_pass"`
    InvoiceLines   []InvoiceLine `json:"invoice_lines"`
    LedgerDigest   string        `json:"ledger_digest"`
}

type Segment struct {
    SegmentIndex int    `json:"segment_index"`
    PlanID       string `json:"plan_id"`
    WindowStart  string `json:"window_start"`
    WindowEnd    string `json:"window_end"`
    SegmentDays  int    `json:"segment_days"`
    BaseCents    int64  `json:"base_cents"`
}
