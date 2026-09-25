package model

// AdmissionGranted and AdmissionDenied are the two admission states of a staged renewal.
const (
	AdmissionGranted = "granted"
	AdmissionDenied  = "denied"
	// CycleDepth marks a row whose lineage walk revisited a token.
	CycleDepth = -1
	// CyclePrefix and OrphanPrefix prefix synthetic lineage roots.
	CyclePrefix  = "cycle:"
	OrphanPrefix = "orphan:"
)

type RenewalEvent struct {
	EventID     string   `json:"event_id"`
	TokenID     string   `json:"token_id"`
	ParentID    string   `json:"parent_id"`
	RenewalSeq  int      `json:"renewal_seq"`
	Mount       string   `json:"mount"`
	Role        string   `json:"role"`
	PolicyNames []string `json:"policy_names"`
	LeaseTTLSec int      `json:"lease_ttl_sec"`
	Renewable   bool     `json:"renewable"`
	Orphan      bool     `json:"orphan"`
	IssuedAt    string   `json:"issued_at"`
}

type PolicyRevision struct {
	EffectiveFrom  string `json:"effective_from"`
	MaxTTLSec      int    `json:"max_ttl_sec"`
	Parent         string `json:"parent"`
	OverrideParent bool   `json:"override_parent"`
	DenyRenew      bool   `json:"deny_renew"`
}

type PolicyDef struct {
	Revisions []PolicyRevision `json:"revisions"`
}

type PoliciesFile struct {
	Policies map[string]PolicyDef `json:"policies"`
}

type MountDef struct {
	MaxLeaseTTLSec      int  `json:"max_lease_ttl_sec"`
	MaxTokenLifetimeSec int  `json:"max_token_lifetime_sec"`
	Renewable           bool `json:"renewable"`
}

type MountsFile struct {
	Mounts map[string]MountDef `json:"mounts"`
}

type RoleDef struct {
	Mount               string `json:"mount"`
	MaxTTLSec           int    `json:"max_ttl_sec"`
	MaxTokenLifetimeSec int    `json:"max_token_lifetime_sec"`
	Renewable           bool   `json:"renewable"`
}

type RolesFile struct {
	Roles map[string]RoleDef `json:"roles"`
}

type StagedLease struct {
	EventID            string `json:"event_id"`
	TokenID            string `json:"token_id"`
	ParentID           string `json:"parent_id"`
	RenewalSeq         int    `json:"renewal_seq"`
	Mount              string `json:"mount"`
	Role               string `json:"role"`
	PolicyCapSec       int    `json:"policy_cap_sec"`
	StaticCapSec       int    `json:"static_cap_sec"`
	LifetimeCeilingSec int    `json:"lifetime_ceiling_sec"`
	BudgetRemainingSec int    `json:"budget_remaining_sec"`
	DelegatedParent    string `json:"delegated_parent"`
	GrantedTTLSec      int    `json:"granted_ttl_sec"`
	Admission          string `json:"admission"`
	EffectiveRenewable bool   `json:"effective_renewable"`
	LineageRoot        string `json:"lineage_root"`
	LineageDepth       int    `json:"lineage_depth"`
	IsOrphan           bool   `json:"is_orphan"`
	IssuedAt           string `json:"issued_at"`
}

type RiskToken struct {
	TokenID          string `json:"token_id"`
	RenewalSeq       int    `json:"renewal_seq"`
	LineageRoot      string `json:"lineage_root"`
	LineageDepth     int    `json:"lineage_depth"`
	IsOrphan         bool   `json:"is_orphan"`
	Admission        string `json:"admission"`
	RiskBucket       string `json:"risk_bucket"`
	RiskScore        int    `json:"risk_score"`
	SecondsRemaining int    `json:"seconds_remaining"`
	ExpiresAt        string `json:"expires_at"`
}

type LineageEdge struct {
	ParentToken string `json:"parent_token"`
	ChildToken  string `json:"child_token"`
}

type LineageRootRow struct {
	LineageRoot  string `json:"lineage_root"`
	TokenCount   int    `json:"token_count"`
	RowCount     int    `json:"row_count"`
	MaxRiskScore int    `json:"max_risk_score"`
	WorstBucket  string `json:"worst_bucket"`
	BlastRadius  int    `json:"blast_radius"`
}

type RiskTotals struct {
	TokenCount         int `json:"token_count"`
	DistinctTokenCount int `json:"distinct_token_count"`
	OrphanCount        int `json:"orphan_count"`
	CriticalCount      int `json:"critical_count"`
	DeniedCount        int `json:"denied_count"`
	CycleCount         int `json:"cycle_count"`
}

type RiskAtlas struct {
	Tokens       []RiskToken      `json:"tokens"`
	LineageEdges []LineageEdge    `json:"lineage_edges"`
	LineageRoots []LineageRootRow `json:"lineage_roots"`
	Totals       RiskTotals       `json:"totals"`
}
