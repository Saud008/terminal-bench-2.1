package model

type RoomType struct {
    RoomTypeID string `json:"room_type_id"`
    Name       string `json:"name"`
    Rank       int    `json:"rank"`
}

type Room struct {
    RoomID     string `json:"room_id"`
    RoomTypeID string `json:"room_type_id"`
    Status     string `json:"status"`
}

type Reservation struct {
    ReservationID string  `json:"reservation_id"`
    GuestID       string  `json:"guest_id"`
    RoomTypeID    string  `json:"room_type_id"`
    LoyaltyTier   string  `json:"loyalty_tier"`
    CancelProb    float64 `json:"cancel_prob"`
    ArrivalRank   int     `json:"arrival_rank"`
}

type Maintenance struct {
    RoomID    string `json:"room_id"`
    StartDate string `json:"start_date"`
    EndDate   string `json:"end_date"`
}

type LoyaltyPolicy struct {
    TierName        string `json:"tier_name"`
    ProtectionRank  int    `json:"protection_rank"`
}

type SubstitutionRule struct {
    FromTypeID string `json:"from_type_id"`
    ToTypeID   string `json:"to_type_id"`
}

type WalkCost struct {
    FromTypeID string `json:"from_type_id"`
    ToTypeID   string `json:"to_type_id"`
    CostCents  int    `json:"cost_cents"`
}

type RoomAssignment struct {
    ReservationID string `json:"reservation_id"`
    GuestID       string `json:"guest_id"`
    RoomID        string `json:"room_id"`
    RoomTypeID    string `json:"room_type_id"`
}

type WalkEntry struct {
    ReservationID string `json:"reservation_id"`
    GuestID       string `json:"guest_id"`
    FromTypeID    string `json:"from_type_id"`
    ToTypeID      string `json:"to_type_id"`
    WalkCostCents int    `json:"walk_cost_cents"`
}

type ScenarioMeta struct {
    Scenario    string `json:"scenario"`
    NightDate   string `json:"night_date"`
    CatalogSeed string `json:"catalog_seed"`
}
