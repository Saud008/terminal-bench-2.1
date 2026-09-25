package model

type Section struct {
    SectionID        string `json:"section_id"`
    Name             string `json:"name"`
    RowCount         int    `json:"row_count"`
    AccessibilityMin int    `json:"accessibility_min"`
}

type Seat struct {
    SeatID     string `json:"seat_id"`
    SectionID  string `json:"section_id"`
    RowNum     int    `json:"row_num"`
    SeatNum    int    `json:"seat_num"`
    Accessible bool   `json:"accessible"`
}

type Order struct {
    OrderID      string `json:"order_id"`
    PatronID     string `json:"patron_id"`
    PaymentRank  int    `json:"payment_rank"`
    CapturedAt   string `json:"captured_at"`
}

type SeatHold struct {
    HoldID    string `json:"hold_id"`
    OrderID   string `json:"order_id"`
    SeatID    string `json:"seat_id"`
    ExpiresAt string `json:"expires_at"`
    Status    string `json:"status"`
}

type Assignment struct {
    HoldID  string `json:"hold_id"`
    SeatID  string `json:"seat_id"`
    OrderID string `json:"order_id"`
    Status  string `json:"status"`
}

type Conflict struct {
    HoldID   string `json:"hold_id"`
    SeatID   string `json:"seat_id"`
    Reason   string `json:"reason"`
    Severity int    `json:"severity"`
}

type ScenarioMeta struct {
    Scenario    string `json:"scenario"`
    EventClock  string `json:"event_clock"`
    CatalogSeed string `json:"catalog_seed"`
}
