package model

type Bundle struct {
	Scenario           string            `json:"scenario"`
	PlanningEpochDay   int               `json:"planning_epoch_day"`
	Permits            []Permit          `json:"permits"`
	Inspectors         []Inspector       `json:"inspectors"`
	ZoningHolds        []ZoningHold      `json:"zoning_holds"`
	BlackoutWindows    []BlackoutWindow  `json:"blackout_windows"`
	Violations         []ViolationRecord `json:"violations"`
	PermitRoutes       []PermitRoute     `json:"permit_routes"`
}

type Permit struct {
	PermitID       string `json:"permit_id"`
	DistrictID     string `json:"district_id"`
	PermitType     string `json:"permit_type"`
	BasePriority   int    `json:"base_priority"`
	RequestedDay   int    `json:"requested_day"`
	Deferred       bool   `json:"deferred"`
}

type Inspector struct {
	InspectorID   string   `json:"inspector_id"`
	CertLevel     int      `json:"cert_level"`
	Districts     []string `json:"districts"`
	DailyCap      int      `json:"daily_cap"`
	AvailableDay  int      `json:"available_day"`
}

type ZoningHold struct {
	DistrictID string `json:"district_id"`
	HoldRank   int    `json:"hold_rank"`
	Active     bool   `json:"active"`
	ReasonCode string `json:"reason_code"`
}

type BlackoutWindow struct {
	DistrictID string `json:"district_id"`
	StartDay   int    `json:"start_day"`
	EndDay     int    `json:"end_day"`
}

type ViolationRecord struct {
	PermitID  string `json:"permit_id"`
	Severity  int    `json:"severity"`
	DaysAgo   int    `json:"days_ago"`
}

type PermitRoute struct {
	PermitType     string `json:"permit_type"`
	InspectionLane string `json:"inspection_lane"`
	MinCertLevel   int    `json:"min_cert_level"`
}
