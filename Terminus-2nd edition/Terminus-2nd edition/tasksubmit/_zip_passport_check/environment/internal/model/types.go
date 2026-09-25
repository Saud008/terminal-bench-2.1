package model

type Scenario struct {
	ScenarioID    string     `json:"scenario_id"`
	ReferenceDate string     `json:"reference_date"`
	Passports     []Passport `json:"passports"`
	Visas         []Visa     `json:"visas"`
	Stamps        []Stamp    `json:"stamps"`
	Rules         []Rule     `json:"rules"`
	Holds         []Hold     `json:"holds"`
	GraceDays     int        `json:"grace_days"`
}

type Passport struct {
	DocID      string `json:"doc_id"`
	HolderID   string `json:"holder_id"`
	IssueDate  string `json:"issue_date"`
	ExpiryDate string `json:"expiry_date"`
	Revoked    bool   `json:"revoked"`
}

type Visa struct {
	DocID      string `json:"doc_id"`
	PassportID string `json:"passport_id"`
	ValidFrom  string `json:"valid_from"`
	ValidTo    string `json:"valid_to"`
	VisaClass  string `json:"visa_class"`
	Revoked    bool   `json:"revoked"`
}

type Stamp struct {
	StampID    string `json:"stamp_id"`
	PassportID string `json:"passport_id"`
	EntryDate  string `json:"entry_date"`
	ExitDate   string `json:"exit_date"`
	PortCode   string `json:"port_code"`
}

type Rule struct {
	RuleID      string `json:"rule_id"`
	Scope       string `json:"scope"`
	PortCode    string `json:"port_code,omitempty"`
	MaxStayDays int    `json:"max_stay_days"`
}

type Hold struct {
	HoldID   string `json:"hold_id"`
	HolderID string `json:"holder_id"`
	Active   bool   `json:"active"`
	Reason   string `json:"reason"`
}

type DecisionRow struct {
	HolderID           string   `json:"holder_id"`
	PassportID         string   `json:"passport_id"`
	VisaID             string   `json:"visa_id"`
	AllowedEntry       bool     `json:"allowed_entry"`
	DenyReasons        []string `json:"deny_reasons"`
	CumulativeStayDays int      `json:"cumulative_stay_days"`
	MaxStayAllowed     int      `json:"max_stay_allowed"`
	RemainingStayDays  int      `json:"remaining_stay_days"`
}

type DecisionReport struct {
	ScenarioID    string        `json:"scenario_id"`
	EvalPass      int           `json:"eval_pass"`
	ReferenceDate string        `json:"reference_date"`
	Decisions     []DecisionRow `json:"decisions"`
	LedgerDigest  string        `json:"ledger_digest"`
}
