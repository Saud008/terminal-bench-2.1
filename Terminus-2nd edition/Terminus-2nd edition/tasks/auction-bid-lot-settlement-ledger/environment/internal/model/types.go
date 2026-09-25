package model

type Scenario struct {
    ScenarioID      string              `json:"scenario_id"`
    Lots            []Lot               `json:"lots"`
    Bids            []Bid               `json:"bids"`
    Deposits        []Deposit           `json:"deposits"`
    PremiumSchedule map[string]Premium  `json:"premium_schedule"`
    Adjustments     []Adjustment        `json:"adjustments"`
}

type Lot struct {
    LotID       string `json:"lot_id"`
    ReserveCents int64  `json:"reserve_cents"`
    Withdrawn   bool   `json:"withdrawn"`
    PremiumTier string `json:"premium_tier"`
}

type Bid struct {
    LotID       string `json:"lot_id"`
    BidderID    string `json:"bidder_id"`
    AmountCents int64  `json:"amount_cents"`
    BidSeq      int    `json:"bid_seq"`
    BidTS       string `json:"bid_ts"`
}

type Deposit struct {
    BidderID      string `json:"bidder_id"`
    DepositCents  int64  `json:"deposit_cents"`
}

type Premium struct {
    RateBPS   int64 `json:"rate_bps"`
    CapCents  int64 `json:"cap_cents"`
}

type Adjustment struct {
    LotID          string `json:"lot_id"`
    BidderID       string `json:"bidder_id"`
    AdjustmentCents int64  `json:"adjustment_cents"`
}

type Award struct {
    LotID        string
    Status       string
    BidderID     string
    HammerCents  int64
}

type InvoiceLine struct {
    LotID           string `json:"lot_id"`
    BidderID        string `json:"bidder_id"`
    HammerCents     int64  `json:"hammer_cents"`
    PremiumCents    int64  `json:"premium_cents"`
    AdjustmentCents int64  `json:"adjustment_cents"`
    DepositApplied  int64  `json:"deposit_applied"`
    AmountDueCents  int64  `json:"amount_due_cents"`
}

type InvoiceReport struct {
    ScenarioID       string        `json:"scenario_id"`
    AdjudicationPass int           `json:"adjudication_pass"`
    Invoices         []InvoiceLine `json:"invoices"`
    LedgerDigest     string        `json:"ledger_digest"`
}
