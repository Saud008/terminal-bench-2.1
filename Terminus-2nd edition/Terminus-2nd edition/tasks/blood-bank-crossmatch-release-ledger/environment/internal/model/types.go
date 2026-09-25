package model

type Scenario struct {
	ScenarioID   string     `json:"scenario_id"`
	ReleaseClock string     `json:"release_clock"`
	Patients     []Patient  `json:"patients"`
	Units        []Unit     `json:"units"`
	Overrides     []Override `json:"overrides"`
}

type Patient struct {
	PatientID  string   `json:"patient_id"`
	ABO        string   `json:"abo"`
	Rh         string   `json:"rh"`
	Antibodies []string `json:"antibodies"`
}

type Unit struct {
	UnitID      string   `json:"unit_id"`
	ABO         string   `json:"abo"`
	Rh          string   `json:"rh"`
	CollectedAt string   `json:"collected_at"`
	ExpiresAt   string   `json:"expires_at"`
	Antigens    []string `json:"antigens"`
}

type Override struct {
	PatientID  string `json:"patient_id"`
	UnitID     string `json:"unit_id"`
	Authorizer string `json:"authorizer"`
	Reason     string `json:"reason"`
	IssuedAt   string `json:"issued_at"`
}

type CrossmatchRow struct {
	PatientID    string   `json:"patient_id"`
	UnitID       string   `json:"unit_id"`
	Compatible   bool     `json:"compatible"`
	FailureCodes []string `json:"failure_codes"`
}

type ReleaseLine struct {
	PatientID       string `json:"patient_id"`
	UnitID          string `json:"unit_id"`
	ReleaseStatus   string `json:"release_status"`
	OverrideApplied bool   `json:"override_applied"`
	Authorizer      string `json:"authorizer"`
	Reason          string `json:"reason"`
}

type ReleaseReport struct {
	ScenarioID     string        `json:"scenario_id"`
	EvaluationPass int           `json:"screening_pass"`
	Releases       []ReleaseLine `json:"releases"`
	LedgerDigest   string        `json:"ledger_digest"`
}
