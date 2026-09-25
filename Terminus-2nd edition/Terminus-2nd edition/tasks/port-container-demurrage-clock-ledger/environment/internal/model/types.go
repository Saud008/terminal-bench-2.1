package model

type Container struct {
	ContainerID string `json:"container_id"`
	CarrierID   string `json:"carrier_id"`
}

type GateEvent struct {
	ContainerID string `json:"container_id"`
	Event       string `json:"event"`
	Ts          string `json:"ts"`
}

type Contract struct {
	ContainerID string `json:"container_id"`
	FreeDays    int    `json:"free_days"`
	Currency    string `json:"currency"`
}

type Hold struct {
	HoldID      string `json:"hold_id"`
	ContainerID string `json:"container_id"`
	Code        string `json:"code"`
	Start       string `json:"start"`
	End         string `json:"end"`
}

type Closure struct {
	Date   string `json:"date"`
	Reason string `json:"reason"`
}

type Tariff struct {
	CarrierID      string `json:"carrier_id"`
	Tier1Days      int    `json:"tier1_days"`
	Tier1RateCents int    `json:"tier1_rate_cents"`
	Tier2RateCents int    `json:"tier2_rate_cents"`
	Tier3RateCents int    `json:"tier3_rate_cents"`
}

type Scenario struct {
	ScenarioID     string      `json:"scenario_id"`
	BillingThrough string      `json:"billing_through"`
	Containers     []Container `json:"containers"`
	GateEvents     []GateEvent `json:"gate_events"`
	Contracts      []Contract  `json:"contracts"`
	Holds          []Hold      `json:"holds"`
	Closures       []Closure   `json:"closures"`
	Tariffs        []Tariff    `json:"tariffs"`
}

type StagedDwell struct {
	ContainerID      string
	EligibleDays     int
	FreeDaysUsed     int
	DemurrageDays    int
	Tier1Days        int
	Tier2Days        int
	Tier3Days        int
	TotalCents       int
	ActiveHold       string
	Currency         string
}

type InvoiceLine struct {
	ContainerID string `json:"container_id"`
	TotalCents  int    `json:"total_cents"`
	Currency    string `json:"currency"`
	Tier1Days   int    `json:"tier1_days"`
	Tier2Days   int    `json:"tier2_days"`
	Tier3Days   int    `json:"tier3_days"`
	ActiveHold  string `json:"active_hold,omitempty"`
}
