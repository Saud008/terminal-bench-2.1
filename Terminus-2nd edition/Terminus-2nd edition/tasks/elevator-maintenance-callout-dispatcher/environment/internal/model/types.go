package model

type AccessWindow struct {
	StartMinute int `json:"start_minute"`
	EndMinute   int `json:"end_minute"`
}

type Building struct {
	BuildingID     string         `json:"building_id"`
	AccessWindows  []AccessWindow `json:"access_windows"`
}

type SLAContract struct {
	Tier                string `json:"tier"`
	BuildingID          string `json:"building_id"`
	MaxResponseMinutes  int    `json:"max_response_minutes"`
	EscalationWeight    int    `json:"escalation_weight"`
	TierRank            int    `json:"tier_rank"`
}

type Fault struct {
	FaultID           string `json:"fault_id"`
	BuildingID        string `json:"building_id"`
	ElevatorBank      string `json:"elevator_bank"`
	FaultCode         string `json:"fault_code"`
	SeverityBase      int    `json:"severity_base"`
	TrappedPassengers int    `json:"trapped_passengers"`
	ReportedMinute    int    `json:"reported_minute"`
	RequiredSkill     int    `json:"required_skill"`
	Cancelled         bool   `json:"cancelled"`
}

type Technician struct {
	TechID      string   `json:"tech_id"`
	SkillLevel  int      `json:"skill_level"`
	ShiftStart  int      `json:"shift_start"`
	ShiftEnd    int      `json:"shift_end"`
	CertTags    []string `json:"cert_tags"`
}

type Bundle struct {
	Seed                string         `json:"seed"`
	Scenario            string         `json:"scenario"`
	RosterEpochMinute int           `json:"roster_epoch_minute"`
	TravelBufferMinutes int            `json:"travel_buffer_minutes"`
	Faults              []Fault        `json:"faults"`
	Technicians         []Technician   `json:"technicians"`
	Buildings           []Building     `json:"buildings"`
	SLAContracts        []SLAContract  `json:"sla_contracts"`
}

type ScoreRow struct {
	FaultID           string
	PriorityScore     int
	SLAUrgency        int
	BreachHorizonMin  int
}

type AssignmentRow struct {
	FaultID       string
	TechID        string
	PlannedMinute int
	Status        string
}
